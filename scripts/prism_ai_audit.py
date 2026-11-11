#!/usr/bin/env python3
"""Read-only weekly audit of a public GitHub repository. Standard library only."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import posixpath
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import PurePosixPath

API = "https://api.github.com"
USER_AGENT = "git-panic-prism-audit/1.0"
MAX_TEXT_FILES = 350
MAX_FILE_BYTES = 500_000
MAX_PAGES = 5
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
TEXT_SUFFIXES = {
    ".md", ".mdx", ".txt", ".yml", ".yaml", ".json", ".toml", ".js",
    ".jsx", ".ts", ".tsx", ".py", ".ps1", ".sh", ".html", ".css",
    ".xml", ".env", ".ini", ".conf", ".properties", ".sql",
}
SKIP_NAMES = {"Cargo.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("credential-assignment", re.compile(
        r"""(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|password)\b\s*[:=]\s*["']([^"']{20,})["']"""
    )),
)
PLACEHOLDER_WORDS = (
    "example", "your_", "replace", "placeholder", "dummy", "sample",
    "changeme", "change-me", "not-a-real", "xxx",
)


class AuditError(Exception):
    pass


class GitHubClient:
    def __init__(self, owner, repo, timeout=20):
        self.owner = owner
        self.repo = repo
        self.timeout = timeout
        self.repo_path = "/repos/{}/{}".format(
            urllib.parse.quote(owner, safe=""),
            urllib.parse.quote(repo, safe=""),
        )

    def read(self, url, accept="application/vnd.github+json"):
        request = urllib.request.Request(
            url, headers={"Accept": accept, "User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            raise AuditError("HTTP {} from {}".format(exc.code, url.split("?")[0])) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AuditError("Request failed for {}".format(url.split("?")[0])) from exc

    def json(self, path):
        url = path if path.startswith("https://") else API + path
        try:
            return json.loads(self.read(url).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AuditError("Invalid JSON from {}".format(url.split("?")[0])) from exc

    def raw_text(self, path, branch):
        url = "https://raw.githubusercontent.com/{}/{}/{}/{}".format(
            urllib.parse.quote(self.owner, safe=""),
            urllib.parse.quote(self.repo, safe=""),
            urllib.parse.quote(branch, safe="/"),
            urllib.parse.quote(path, safe="/"),
        )
        return self.read(url, "text/plain").decode("utf-8", errors="replace")

    def collection(self, endpoint):
        items = []
        capped = False
        for page in range(1, MAX_PAGES + 1):
            sep = "&" if "?" in endpoint else "?"
            batch = self.json("{}{}per_page=100&page={}".format(endpoint, sep, page))
            if not isinstance(batch, list):
                raise AuditError("Expected a list from {}".format(endpoint))
            items.extend(batch)
            if len(batch) < 100:
                return items, capped
        return items, True

    def probe(self, url):
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code
        except (urllib.error.URLError, TimeoutError, OSError):
            return None


def parse_time(value):
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except (ValueError, AttributeError):
        return None


def days_old(value, now):
    parsed = parse_time(value)
    return None if parsed is None else max(0, (now - parsed).days)


def safe_title(value):
    return html.escape(re.sub(r"\s+", " ", str(value or "")).strip()[:240], quote=False)


def heading_anchors(markdown):
    anchors, used = set(), {}
    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading = match.group(2).replace(chr(96), "")
        heading = re.sub(r"[*_~]", "", html.unescape(heading).lower())
        slug = re.sub(r"[^\w -]", "", heading, flags=re.UNICODE)
        slug = re.sub(r"\s", "-", slug.strip())
        if slug:
            count = used.get(slug, 0)
            used[slug] = count + 1
            anchors.add(slug if count == 0 else "{}-{}".format(slug, count))
    return anchors


def resolve_relative_link(source, target, tracked_paths, anchors_by_path):
    raw = target.strip()
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return None
    path_part = urllib.parse.unquote(parsed.path)
    fragment = urllib.parse.unquote(parsed.fragment)
    if path_part.startswith("/"):
        candidate = posixpath.normpath(path_part.lstrip("/"))
    elif path_part:
        candidate = posixpath.normpath(posixpath.join(posixpath.dirname(source), path_part))
    else:
        candidate = source
    exists = candidate in tracked_paths
    if not exists:
        exists = any(path.startswith(candidate.rstrip("/") + "/") for path in tracked_paths)
        if not exists and not PurePosixPath(candidate).suffix:
            for index_name in ("README.md", "index.md", "index.html"):
                index_path = posixpath.join(candidate, index_name)
                if index_path in tracked_paths:
                    candidate, exists = index_path, True
                    break
    if not exists:
        return "missing target: {}".format(path_part or source)
    if fragment and candidate.lower().endswith((".md", ".mdx")):
        known = anchors_by_path.get(candidate)
        if known is not None and fragment.lower() not in known:
            return "missing heading #{} in {}".format(fragment, candidate)
    return None


def check_markdown_links(markdown_files, tracked_paths):
    anchors = {path: heading_anchors(body) for path, body in markdown_files.items()}
    broken, external, checked = [], 0, 0
    for source, body in markdown_files.items():
        for match in LINK_RE.finditer(body):
            raw = match.group(1).strip()
            if raw.startswith("<") and ">" in raw:
                target = raw[1:raw.index(">")]
            else:
                target = raw.split()[0] if raw.split() else ""
            if not target:
                continue
            parts = urllib.parse.urlsplit(target)
            if parts.scheme or parts.netloc:
                external += 1
                continue
            checked += 1
            problem = resolve_relative_link(source, target, tracked_paths, anchors)
            if problem:
                broken.append({
                    "source": source,
                    "line": body.count("\n", 0, match.start()) + 1,
                    "target": target,
                    "problem": problem,
                })
    return {"checked": checked, "external": external, "broken": broken}


def scan_secret_candidates(path, body):
    hits = []
    for line_number, line in enumerate(body.splitlines(), 1):
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(line):
                value = match.group(1) if match.lastindex else match.group(0)
                if any(word in value.lower() for word in PLACEHOLDER_WORDS):
                    continue
                hits.append({"path": path, "line": line_number, "detector": name})
                break
    return hits


def is_scannable_text(path, size):
    name = PurePosixPath(path).name
    return (
        size <= MAX_FILE_BYTES
        and (PurePosixPath(path).suffix.lower() in TEXT_SUFFIXES
             or name in {".gitignore", ".gitattributes", ".env"} or name.startswith(".env."))
        and name not in SKIP_NAMES
    )


def fetch_text_files(client, paths, branch):
    output, failures = {}, []
    def fetch_one(path):
        try:
            return path, client.raw_text(path, branch), None
        except AuditError as exc:
            return path, None, str(exc)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for future in concurrent.futures.as_completed(
            [pool.submit(fetch_one, path) for path in paths]
        ):
            path, body, error = future.result()
            if error:
                failures.append({"path": path, "error": error})
            else:
                output[path] = body
    return output, failures


def add_finding(findings, severity, title, detail, url=None):
    findings.append({"severity": severity, "title": title, "detail": detail, "url": url})


def audit(owner, repo_name):
    client = GitHubClient(owner, repo_name)
    findings, coverage = [], []
    checked_at = dt.datetime.now(dt.timezone.utc)
    result = {
        "owner": owner, "repo": repo_name,
        "url": "https://github.com/{}/{}".format(owner, repo_name),
        "checked_at": checked_at.isoformat(timespec="seconds"),
        "findings": findings, "coverage": coverage,
    }
    repository = client.json(client.repo_path)
    default_branch = repository.get("default_branch") or "main"
    result["repository"], result["default_branch"] = repository, default_branch

    branches = []
    try:
        branches, _ = client.collection(client.repo_path + "/branches")
        result["branches"] = branches
    except AuditError as exc:
        coverage.append("Branch listing unavailable: {}".format(exc))
    default_info = next((b for b in branches if b.get("name") == default_branch), None)
    if default_info is None:
        add_finding(findings, "MEDIUM", "Default branch protection unavailable",
                    "The default branch could not be matched in the branch listing.")
    elif not default_info.get("protected", False):
        add_finding(findings, "MEDIUM", "Default branch is not protected",
                    "The {} branch is reported as unprotected. Consider requiring review and CI checks.".format(default_branch),
                    result["url"] + "/settings/branches")

    tree_data = client.json(client.repo_path + "/git/trees/{}?recursive=1".format(
        urllib.parse.quote(default_branch, safe="")
    ))
    entries = tree_data.get("tree", [])
    tracked = {e.get("path") for e in entries if e.get("type") == "blob" and e.get("path")}
    truncated = bool(tree_data.get("truncated"))
    result["tree_file_count"], result["tree_truncated"] = len(tracked), truncated
    if truncated:
        add_finding(findings, "MEDIUM", "Repository tree response was truncated",
                    "GitHub truncated the recursive tree; file checks are incomplete.")

    workflow_paths = sorted(p for p in tracked if p.startswith(".github/workflows/")
                             and p.lower().endswith((".yml", ".yaml")))
    result["workflow_file_paths"] = workflow_paths
    try:
        workflows = client.json(client.repo_path + "/actions/workflows").get("workflows", [])
        result["workflows"] = workflows
    except AuditError as exc:
        result["workflows"] = []
        coverage.append("Workflow inventory unavailable: {}".format(exc))
    try:
        runs = client.json(client.repo_path + "/actions/runs?per_page=50").get("workflow_runs", [])
        result["workflow_runs"] = runs
    except AuditError as exc:
        runs = []
        result["workflow_runs"] = []
        coverage.append("Actions run history unavailable: {}".format(exc))
    if not runs:
        add_finding(findings, "LOW", "No workflow runs returned",
                    "Actions run history was empty or unavailable; CI health could not be confirmed.",
                    result["url"] + "/actions")
    else:
        failed = []
        for run in runs:
            created = parse_time(run.get("created_at"))
            if created and (checked_at - created).days <= 30 and run.get("conclusion") in {
                "failure", "timed_out", "action_required"
            }:
                failed.append(run)
        if failed:
            latest = max(failed, key=lambda r: r.get("created_at") or "")
            add_finding(findings, "HIGH", "Recent GitHub Actions failure",
                        "{} failed, timed-out, or action-required run(s) in the last 30 days; latest: {}.".format(
                            len(failed), latest.get("display_title") or latest.get("name")),
                        latest.get("html_url") or result["url"] + "/actions")
        else:
            add_finding(findings, "INFO", "No recent failed workflow runs observed",
                        "No failed, timed-out, or action-required run was returned in the last 30 days.",
                        result["url"] + "/actions")

    try:
        releases, _ = client.collection(client.repo_path + "/releases")
        result["releases"] = releases
    except AuditError as exc:
        releases = []
        result["releases"] = []
        coverage.append("Release history unavailable: {}".format(exc))
    if not releases:
        add_finding(findings, "INFO", "No published releases returned",
                    "The repository has no published releases in the returned API data.",
                    result["url"] + "/releases")
    else:
        latest = releases[0]
        result["latest_release"] = latest
        missing_digests = [a for a in latest.get("assets", []) if not a.get("digest")]
        if missing_digests:
            add_finding(findings, "LOW", "Latest release assets without GitHub digests",
                        "{} asset(s) in the latest release do not expose a GitHub-provided digest.".format(
                            len(missing_digests)),
                        latest.get("html_url") or result["url"] + "/releases")

    try:
        issues, issues_capped = client.collection(client.repo_path + "/issues?state=open")
        issues = [i for i in issues if "pull_request" not in i]
        result["open_issues"], result["issues_capped"] = issues, issues_capped
    except AuditError as exc:
        issues = []
        result["open_issues"] = []
        coverage.append("Open issue listing unavailable: {}".format(exc))
    try:
        pulls, pulls_capped = client.collection(client.repo_path + "/pulls?state=open")
        result["open_pulls"], result["pulls_capped"] = pulls, pulls_capped
    except AuditError as exc:
        pulls = []
        result["open_pulls"] = []
        coverage.append("Open pull-request listing unavailable: {}".format(exc))
    for kind, items in (("issue", issues), ("pull request", pulls)):
        old = [i for i in items if (days_old(i.get("updated_at"), checked_at) or 0) >= 30]
        if old:
            add_finding(findings, "LOW", "Stale open {}s".format(kind),
                        "{} open {}(s) have not been updated for at least 30 days.".format(len(old), kind),
                        result["url"] + ("/issues" if kind == "issue" else "/pulls"))

    security = repository.get("security_and_analysis") or {}
    result["security"] = security
    security_flags = {
        "secret_scanning": ("Secret scanning", "HIGH"),
        "secret_scanning_push_protection": ("Secret scanning push protection", "HIGH"),
        "dependabot_security_updates": ("Dependabot security updates", "MEDIUM"),
    }
    for key, (label, severity) in security_flags.items():
        status = (security.get(key) or {}).get("status")
        if status == "disabled":
            add_finding(findings, severity, "{} disabled".format(label),
                        "GitHub reports this repository feature as disabled.",
                        result["url"] + "/settings/security_analysis")
        elif status == "enabled":
            add_finding(findings, "INFO", "{} enabled".format(label),
                        "GitHub reports this repository feature as enabled.",
                        result["url"] + "/settings/security_analysis")
        else:
            coverage.append("{} status was not exposed by repository metadata.".format(label))
    non_provider = (security.get("secret_scanning_non_provider_patterns") or {}).get("status")
    if non_provider == "disabled":
        add_finding(findings, "LOW", "Non-provider secret pattern scanning disabled",
                    "GitHub reports non-provider pattern scanning as disabled; the local heuristic scan is separate.",
                    result["url"] + "/settings/security_analysis")

    homepage = repository.get("homepage")
    if homepage:
        status = client.probe(homepage)
        result["homepage_status"] = status
        if status is None or status >= 400:
            add_finding(findings, "MEDIUM", "Repository homepage did not respond successfully",
                        "The configured homepage returned {} to a HEAD request.".format(
                            "no HTTP response" if status is None else status), homepage)
        else:
            add_finding(findings, "INFO", "Repository homepage responds",
                        "The configured homepage returned HTTP {}.".format(status), homepage)
    else:
        result["homepage_status"] = None
        add_finding(findings, "LOW", "No repository homepage configured",
                    "GitHub repository metadata does not expose a homepage URL.",
                    result["url"] + "/settings")

    eligible = [e for e in entries if e.get("type") == "blob"
                and is_scannable_text(e.get("path", ""), e.get("size", 0) or 0)]
    eligible.sort(key=lambda e: (
        0 if e.get("path", "").lower() in {"readme.md", "security.md", "contributing.md"} else 1,
        e.get("path", ""),
    ))
    skipped = max(0, len(eligible) - MAX_TEXT_FILES)
    selected = [e["path"] for e in eligible[:MAX_TEXT_FILES]]
    texts, fetch_failures = fetch_text_files(client, selected, default_branch)
    coverage.append("Fetched {} of {} eligible text files.".format(len(texts), len(eligible)))
    if skipped:
        coverage.append("{} eligible files were beyond the {}-file cap.".format(skipped, MAX_TEXT_FILES))
    if fetch_failures:
        coverage.append("{} file(s) could not be fetched.".format(len(fetch_failures)))
    if skipped or fetch_failures or truncated:
        add_finding(findings, "MEDIUM", "Tracked text-file scan coverage incomplete",
                    "Some text files were skipped, could not be fetched, or were omitted by a truncated tree.")

    markdown = {p: body for p, body in texts.items() if p.lower().endswith((".md", ".mdx"))}
    links = check_markdown_links(markdown, tracked)
    result["link_results"] = links
    if links["broken"]:
        add_finding(findings, "MEDIUM", "Broken relative documentation links found",
                    "{} broken relative links found across {} Markdown files.".format(
                        len(links["broken"]), len(markdown)), result["url"])
    else:
        add_finding(findings, "INFO", "No broken relative Markdown links observed",
                    "{} relative links checked in {} Markdown files; {} external links were not fetched.".format(
                        links["checked"], len(markdown), links["external"]), result["url"])

    hits = []
    for path, body in texts.items():
        hits.extend(scan_secret_candidates(path, body))
    result["secret_scan"] = {
        "scanned_files": len(texts), "eligible_files": len(eligible),
        "skipped_files": skipped, "fetch_failures": len(fetch_failures), "hits": hits,
    }
    if hits:
        add_finding(findings, "CRITICAL", "Potential credential pattern detected",
                    "{} match(es) detected. Report shows only file paths, line numbers, and detector names; values are never printed.".format(
                        len(hits)), result["url"])
    else:
        add_finding(findings, "INFO", "No configured credential patterns matched",
                    "No configured high-confidence patterns matched in fetched text files. This is not proof that no secret exists.",
                    result["url"])

    support_text = "\n".join(body for path, body in markdown.items())
    if re.search(r"\b24[\s-]?(?:hours?|h)\b|\bone business day\b", support_text, re.I):
        result["support_commitment"] = "A 24-hour or one-business-day reference was found in scanned Markdown."
    else:
        result["support_commitment"] = "No 24-hour or one-business-day response commitment was found in scanned Markdown."
        add_finding(findings, "LOW", "No 24-hour support commitment documented",
                    "No 24-hour or one-business-day response commitment was detected in scanned Markdown.",
                    result["url"])
    return result


def render_report(data):
    findings = sorted(data["findings"], key=lambda f: (
        SEVERITY_ORDER.get(f["severity"], 9), f["title"]
    ))
    counts = {key: 0 for key in SEVERITY_ORDER}
    for item in findings:
        counts[item["severity"]] += 1
    overall = (
        "ATTENTION REQUIRED" if counts["CRITICAL"] or counts["HIGH"]
        else "REVIEW RECOMMENDED" if counts["MEDIUM"]
        else "NO HIGH-RISK FINDINGS OBSERVED"
    )
    repo = data["repository"]
    branch_sha = next((b.get("commit", {}).get("sha") for b in data.get("branches", [])
                       if b.get("name") == data["default_branch"]), "not returned")
    lines = [
        "# Prism AI weekly repository audit", "",
        "- **Overall:** {}".format(overall),
        "- **Checked:** {}".format(data["checked_at"]),
        "- **Repository:** [{}/{}]({})".format(data["owner"], data["repo"], data["url"]),
        "- **Default branch:** {}".format(data["default_branch"]),
        "- **Default branch commit:** {}".format(branch_sha),
        "- **Findings:** " + ", ".join("{} {}".format(n, s.lower()) for s, n in counts.items() if n),
        "",
        "Read-only report. No issues, comments, branches, commits, releases, or settings were changed in Prism AI.",
        "", "## Findings", "",
    ]
    if not findings:
        lines.append("No findings were recorded.")
    for item in findings:
        title = "**{}: {}**".format(item["severity"], item["title"])
        lines.extend([
            "[{}]({})".format(title, item["url"]) if item.get("url") else title,
            "", item["detail"], "",
        ])
    lines.extend([
        "## Repository snapshot", "",
        "- Description: {}".format(safe_title(repo.get("description")) or "not set"),
        "- Visibility: {}".format(repo.get("visibility") or ("private" if repo.get("private") else "public")),
        "- License: {}".format((repo.get("license") or {}).get("spdx_id") or "not reported"),
        "- Stars / forks: {} / {}".format(repo.get("stargazers_count", 0), repo.get("forks_count", 0)),
        "- Topics: {}".format(", ".join(repo.get("topics") or []) or "none"),
        "- Tracked files: {}".format(data.get("tree_file_count", "unknown")),
        "- Workflow files: {}".format(len(data.get("workflow_file_paths", []))),
        "- GitHub workflows listed: {}".format(len(data.get("workflows", []))),
        "- Open issues: {}".format(len(data.get("open_issues", []))),
        "- Open pull requests: {}".format(len(data.get("open_pulls", []))),
        "- Releases returned: {}".format(len(data.get("releases", []))),
        "- Homepage HTTP status: {}".format(data.get("homepage_status", "not checked")),
        "", "## Recent workflow runs", "",
    ])
    runs = data.get("workflow_runs", [])
    if not runs:
        lines.append("No workflow runs were returned.")
    for run in runs[:10]:
        lines.append("- [{} / {}]({}) — {} — {}".format(
            safe_title(run.get("name") or "workflow"),
            run.get("run_number", "?"),
            run.get("html_url") or data["url"] + "/actions",
            run.get("conclusion") or run.get("status") or "unknown",
            safe_title(run.get("display_title") or run.get("name")),
        ))
    for title, key, route in (
        ("Open issues", "open_issues", "issues"),
        ("Open pull requests", "open_pulls", "pulls"),
    ):
        lines.extend(["", "## {}".format(title), ""])
        items = data.get(key, [])
        if not items:
            lines.append("No open items returned.")
        for item in items[:20]:
            lines.append("- [#{}: {}]({}) — updated {}".format(
                item.get("number"), safe_title(item.get("title")),
                item.get("html_url") or data["url"] + "/" + route,
                (item.get("updated_at") or "unknown")[:10],
            ))
    links = data.get("link_results", {})
    lines.extend([
        "", "## Documentation link check", "",
        "- Relative links checked: {}; external links not fetched: {}; broken relative links: {}.".format(
            links.get("checked", 0), links.get("external", 0), len(links.get("broken", []))),
    ])
    for item in links.get("broken", [])[:100]:
        lines.append("- {}:{} -> {} ({})".format(
            item["source"], item["line"], item["target"], item["problem"]))
    scan = data.get("secret_scan", {})
    lines.extend([
        "", "## Credential pattern scan", "",
        "- Files fetched: {}; eligible text files: {}; possible matches: {}.".format(
            scan.get("scanned_files", 0), scan.get("eligible_files", 0), len(scan.get("hits", []))),
        "- Candidate secret values are never printed.",
    ])
    for hit in scan.get("hits", [])[:100]:
        lines.append("- {}:{} — detector {}".format(hit["path"], hit["line"], hit["detector"]))
    lines.extend([
        "", "## Coverage and limitations", "",
        "- External Markdown links are counted but not followed.",
        "- Credential scanning is heuristic and limited to fetched tracked text files under file-size and file-count caps.",
        "- Unavailable GitHub settings are reported as unavailable, not as passing.",
        "- Release binaries are not downloaded or independently re-hashed.",
        "- Runtime application behavior, private alerts, account-level settings, and actual response performance are not verified.",
    ])
    lines.extend("- {}".format(note) for note in data.get("coverage", []))
    lines.extend([
        "", "## Audit scope", "",
        "The workflow reads public GitHub metadata and file contents for DudeSquad999/Prism-Ai. It writes only an Actions summary and report artifact in git-panic.", "",
    ])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="DudeSquad999")
    parser.add_argument("--repo", default="Prism-Ai")
    parser.add_argument("--output", help="Write the Markdown report to this path.")
    args = parser.parse_args(argv)
    try:
        data = audit(args.owner, args.repo)
    except AuditError as exc:
        print("Audit failed: {}".format(exc), file=sys.stderr)
        return 2
    report = render_report(data)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(report)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
