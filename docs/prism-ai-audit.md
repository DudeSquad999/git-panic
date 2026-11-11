# Prism AI weekly audit

This workflow adds a scheduled, read-only audit of the public repository
DudeSquad999/Prism-Ai. It is hosted in git-panic so the Prism AI repository is
not modified.

## Schedule and manual runs

The workflow runs every Tuesday at 14:00 UTC. This corresponds to 09:00 Eastern
Standard Time and 10:00 Eastern Daylight Time. It can also be started manually
from the Actions tab with workflow_dispatch.

The first scheduled run occurs only after this workflow is merged into the
default branch of git-panic. Pull requests and pushes to main run unit tests
and Python syntax checks, not the scheduled audit.

## What it checks

- Repository metadata, default branch protection, branch and commit snapshots,
  About description/topics, license, homepage, releases, issues, and PRs.
- GitHub Actions run health and the latest Pages-related deployment result.
- README installer command, pinned installer version and URL, published EXE
  asset, and expected SHA-256 versus GitHub's release digest metadata.
- Relative Markdown links, local heading anchors, available YAML syntax checks,
  and em dash/emoji scans in Markdown.
- Publicly exposed secret-scanning, push-protection, and Dependabot settings,
  plus high-confidence credential patterns in fetched tracked text files.
- Architecture/project-structure documentation, runbook presence, and a known
  browser-preview documentation consistency check.
- Whether a 24-hour or one-business-day support acknowledgement commitment
  appears in scanned Markdown documentation.

Potential credentials are never printed. Reports include only file paths, line
numbers, and detector names.

## Permissions and write boundaries

The workflow declares only contents:read permission for its own repository.
It queries the public Prism AI repository through unauthenticated HTTPS GET and
HEAD requests. It does not use a Prism AI token, read repository secrets, or
write issues, comments, branches, commits, releases, settings, or files in
Prism-Ai.

The only generated output is a Markdown audit report in the git-panic Actions
summary and a 90-day Actions artifact. The workflow does not repair findings.

## Running locally

From the git-panic repository root, run:

    python scripts/prism_ai_audit.py

To write a report to a file:

    python scripts/prism_ai_audit.py --output prism-ai-audit.md

The script uses only the Python standard library. Unit tests can be run with:

    python -m unittest discover -s tests -p "test_prism_ai_audit.py" -v

## Limitations

This is a monitoring and triage report, not a security certification.

- Credential matching is heuristic. A clean scan does not prove that no secret
  exists, and only fetched tracked text files under configured size and count
  limits are checked.
- External Markdown links are counted but not fetched.
- GitHub may hide settings or API data based on the current access level. An
  unavailable check is reported as unavailable, not treated as a pass.
- YAML parsing uses PyYAML only when available in the runner; otherwise the
  result is explicitly marked unavailable.
- Typography scans cover common emoji Unicode ranges and em dashes in fetched
  Markdown. They are automated checks, not a complete language/style review.
- The report does not download or independently re-hash release binaries; it
  compares the install script digest with GitHub's published asset digest.
- It cannot validate desktop application behavior, private Dependabot alerts,
  account-level settings, or actual support response performance.
- No issue, pull request, commit, release, or configuration is automatically
  changed based on an audit finding. Remediation requires a separate review.

## Interpreting results

Critical and high findings require attention. Medium findings identify
meaningful maintenance or coverage risks. Low findings are recommendations or
documentation gaps. Informational findings record observed state. The report
separates missing evidence from verified failures and records incomplete scan
coverage.
