//! Black-box tests that run the compiled `git-panic` binary against throwaway
//! repositories in OS temporary directories. Nothing here touches a real
//! working repository. Fixture identities are fake and hooks are disabled.

use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Repo {
    path: PathBuf,
}

impl Repo {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "git-panic-cli-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir_all(&path).unwrap();
        let repo = Repo { path };
        repo.git(&["init", "-q", "-b", "main"]);
        repo.git(&["config", "user.name", "Fixture"]);
        repo.git(&["config", "user.email", "fixture@example.invalid"]);
        repo.git(&["config", "commit.gpgsign", "false"]);
        repo.git(&["config", "core.hooksPath", "/dev/null"]);
        repo
    }

    fn git(&self, args: &[&str]) -> String {
        let out = Command::new("git")
            .args(args)
            .current_dir(&self.path)
            .env("GIT_CONFIG_GLOBAL", "/dev/null")
            .env("GIT_CONFIG_SYSTEM", "/dev/null")
            .output()
            .unwrap();
        assert!(
            out.status.success(),
            "git {:?} failed: {}",
            args,
            String::from_utf8_lossy(&out.stderr)
        );
        String::from_utf8(out.stdout).unwrap().trim().to_string()
    }

    fn commit_file(&self, name: &str, content: &str, message: &str) -> String {
        std::fs::write(self.path.join(name), content).unwrap();
        self.git(&["add", name]);
        self.git(&["commit", "-q", "-m", message]);
        self.git(&["rev-parse", "HEAD"])
    }

    fn run(&self, args: &[&str]) -> Output {
        run_in(&self.path, args)
    }

    /// Everything a read-only or branch-only operation must not change.
    fn snapshot(&self) -> State {
        State {
            head: self.git(&["rev-parse", "HEAD"]),
            head_ref: self.git(&["symbolic-ref", "-q", "--short", "HEAD"]),
            status: self.git(&["status", "--porcelain=v1", "--untracked-files=all"]),
            refs: self.git(&["for-each-ref", "--format=%(refname) %(objectname)"]),
            index: self.git(&["ls-files", "--stage"]),
            reflog: self.git(&["reflog", "--format=%H %gs"]),
            files: std::fs::read_to_string(self.path.join("a.txt")).unwrap_or_default(),
        }
    }
}

impl Drop for Repo {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.path);
    }
}

#[derive(Debug, PartialEq)]
struct State {
    head: String,
    head_ref: String,
    status: String,
    refs: String,
    index: String,
    reflog: String,
    files: String,
}

fn run_in(dir: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_git-panic"))
        .args(args)
        .current_dir(dir)
        .stdin(Stdio::null())
        .output()
        .unwrap()
}

fn stdout(out: &Output) -> String {
    String::from_utf8_lossy(&out.stdout).to_string()
}

fn stderr(out: &Output) -> String {
    String::from_utf8_lossy(&out.stderr).to_string()
}

#[test]
fn outside_a_repository_fails_with_actionable_message() {
    let dir = std::env::temp_dir().join(format!("git-panic-norepo-{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    // GIT_CEILING_DIRECTORIES stops discovery from finding a parent repository.
    let out = Command::new(env!("CARGO_BIN_EXE_git-panic"))
        .arg("reset")
        .current_dir(&dir)
        .env("GIT_CEILING_DIRECTORIES", std::env::temp_dir())
        .stdin(Stdio::null())
        .output()
        .unwrap();
    let _ = std::fs::remove_dir_all(&dir);
    assert_eq!(out.status.code(), Some(1));
    assert!(stderr(&out).contains("No Git repository found"));
    assert!(stdout(&out).is_empty());
}

#[test]
fn empty_repository_search_reports_empty_reflog_not_no_match() {
    let repo = Repo::new();
    let out = repo.run(&["reset"]);
    assert_eq!(out.status.code(), Some(0));
    assert!(stdout(&out).contains("No local HEAD reflog entries"));
    let json = repo.run(&["--json", "reset"]);
    assert_eq!(json.status.code(), Some(0));
    assert!(stdout(&json).contains("\"match_count\":0"));
}

#[test]
fn search_reports_total_when_nothing_matches() {
    let repo = Repo::new();
    repo.commit_file("a.txt", "one", "first");
    let out = repo.run(&["zzz-not-present"]);
    assert_eq!(out.status.code(), Some(0));
    assert!(stdout(&out).contains("No matching HEAD reflog entries among 1 total"));
}

#[test]
fn search_is_literal_not_regex() {
    let repo = Repo::new();
    repo.commit_file("a.txt", "one", "first");
    let out = repo.run(&[".*"]);
    assert!(stdout(&out).contains("No matching"));
}

#[test]
fn blank_search_and_query_with_subcommand_fail_nonzero() {
    let repo = Repo::new();
    repo.commit_file("a.txt", "one", "first");
    assert_eq!(repo.run(&["   "]).status.code(), Some(1));
    assert_eq!(repo.run(&["reset", "tui"]).status.code(), Some(1));
}

#[test]
fn tui_without_a_terminal_fails_instead_of_hanging() {
    let repo = Repo::new();
    repo.commit_file("a.txt", "one", "first");
    for args in [&[][..], &["tui"][..]] {
        let out = repo.run(args);
        assert_eq!(out.status.code(), Some(1), "args {args:?}");
        assert!(stderr(&out).contains("interactive terminal"));
    }
}

#[test]
fn json_flag_rejected_for_tui_and_bare_invocation() {
    let repo = Repo::new();
    repo.commit_file("a.txt", "one", "first");
    for args in [&["--json"][..], &["tui", "--json"][..]] {
        let out = repo.run(args);
        assert_eq!(out.status.code(), Some(1), "args {args:?}");
        assert!(stdout(&out).is_empty());
    }
}

#[test]
fn json_search_is_parseable_and_matches_text_results() {
    let repo = Repo::new();
    let first = repo.commit_file("a.txt", "one", "demo: first");
    repo.commit_file("a.txt", "two", "demo: second");
    let out = repo.run(&["--json", "demo:"]);
    assert_eq!(out.status.code(), Some(0));
    let v: serde_json::Value = serde_json::from_str(stdout(&out).trim()).unwrap();
    assert_eq!(v["match_count"], 2);
    assert_eq!(v["matches"][1]["oid"], first);
    assert_eq!(stdout(&out).trim().lines().count(), 1, "one JSON document");
}

#[test]
fn preview_changes_nothing_and_create_only_adds_one_branch() {
    let repo = Repo::new();
    let first = repo.commit_file("a.txt", "one", "first");
    repo.commit_file("a.txt", "two", "second");
    // Staged, unstaged and untracked work must all survive.
    std::fs::write(repo.path.join("staged.txt"), "staged").unwrap();
    repo.git(&["add", "staged.txt"]);
    std::fs::write(repo.path.join("staged.txt"), "staged then edited").unwrap();
    std::fs::write(repo.path.join("untracked.txt"), "untracked").unwrap();
    std::fs::write(repo.path.join("a.txt"), "two plus edits").unwrap();

    let before = repo.snapshot();
    let preview = repo.run(&["recover", &first, "--branch", "panic/demo"]);
    assert_eq!(preview.status.code(), Some(0));
    assert!(stdout(&preview).contains("Preview only"));
    assert_eq!(repo.snapshot(), before, "preview must not change anything");

    let created = repo.run(&["recover", &first, "--branch", "panic/demo", "--create"]);
    assert_eq!(created.status.code(), Some(0));
    let after = repo.snapshot();
    assert_eq!(after.head, before.head, "HEAD commit unchanged");
    assert_eq!(after.head_ref, before.head_ref, "current branch unchanged");
    assert_eq!(
        after.status, before.status,
        "staged/unstaged/untracked intact"
    );
    assert_eq!(after.index, before.index, "index unchanged");
    assert_eq!(after.files, before.files, "working file unchanged");
    assert_eq!(
        after.refs,
        format!("{}\nrefs/heads/panic/demo {first}", before.refs),
        "exactly one new ref"
    );
    assert_eq!(repo.git(&["rev-parse", "panic/demo"]), first);
}

#[test]
fn existing_branch_is_never_overwritten() {
    let repo = Repo::new();
    let first = repo.commit_file("a.txt", "one", "first");
    let second = repo.commit_file("a.txt", "two", "second");
    repo.git(&["branch", "keep-me", &second]);
    let before = repo.snapshot();
    for extra in [&[][..], &["--create"][..]] {
        let mut args = vec!["recover", first.as_str(), "--branch", "keep-me"];
        args.extend_from_slice(extra);
        let out = repo.run(&args);
        assert_eq!(out.status.code(), Some(1));
        assert!(stderr(&out).contains("already exists"));
    }
    assert_eq!(repo.snapshot(), before);
    assert_eq!(repo.git(&["rev-parse", "keep-me"]), second);
}

#[test]
fn invalid_targets_and_names_fail_without_writing() {
    let repo = Repo::new();
    let first = repo.commit_file("a.txt", "one", "first");
    let tree = repo.git(&["rev-parse", "HEAD^{tree}"]);
    let before = repo.snapshot();
    let zero = "0".repeat(40);
    let cases: Vec<(String, String)> = vec![
        ("HEAD@{0}".into(), "panic/x".into()),
        ("abc123".into(), "panic/x".into()),
        (zero, "panic/x".into()),
        (tree, "panic/x".into()), // exists, but is a tree, not a commit
        (first.clone(), "HEAD".into()),
        (first.clone(), "bad name".into()),
        (first.clone(), "a..b".into()),
        (first.clone(), "x.lock".into()),
        (first.clone(), "".into()),
    ];
    for (oid, branch) in cases {
        for create in [false, true] {
            let mut args = vec!["recover", oid.as_str(), "--branch", branch.as_str()];
            if create {
                args.push("--create");
            }
            let out = repo.run(&args);
            assert_eq!(
                out.status.code(),
                Some(1),
                "oid={oid:?} branch={branch:?} create={create}"
            );
        }
    }
    assert_eq!(repo.snapshot(), before);
}

#[test]
fn works_with_detached_head_and_does_not_reattach() {
    let repo = Repo::new();
    let first = repo.commit_file("a.txt", "one", "first");
    repo.commit_file("a.txt", "two", "second");
    repo.git(&["checkout", "-q", "--detach", &first]);
    let out = repo.run(&["recover", &first, "--branch", "panic/detached", "--create"]);
    assert_eq!(out.status.code(), Some(0));
    assert_eq!(repo.git(&["rev-parse", "HEAD"]), first);
    let head = Command::new("git")
        .args(["symbolic-ref", "-q", "HEAD"])
        .current_dir(&repo.path)
        .output()
        .unwrap();
    assert!(!head.status.success(), "HEAD must stay detached");
}

#[test]
fn reset_mistake_can_be_found_and_preserved_end_to_end() {
    let repo = Repo::new();
    repo.commit_file("a.txt", "one", "demo: first");
    let lost = repo.commit_file("a.txt", "two", "demo: second");
    repo.git(&["reset", "-q", "--hard", "HEAD~1"]);
    assert_ne!(repo.git(&["rev-parse", "HEAD"]), lost);

    let found = repo.run(&["--json", "demo: second"]);
    let v: serde_json::Value = serde_json::from_str(stdout(&found).trim()).unwrap();
    assert_eq!(v["matches"][0]["oid"], lost);

    let out = repo.run(&["recover", &lost, "--branch", "panic/lost", "--create"]);
    assert_eq!(out.status.code(), Some(0));
    assert_eq!(repo.git(&["rev-parse", "panic/lost"]), lost);
    // Branch preservation does not restore files: the working copy stays at "one".
    assert_eq!(
        std::fs::read_to_string(repo.path.join("a.txt")).unwrap(),
        "one"
    );
}

#[test]
fn snapshot_stays_an_explicit_failure() {
    let repo = Repo::new();
    repo.commit_file("a.txt", "one", "first");
    let out = repo.run(&["snapshot", "--before", "yesterday"]);
    assert_eq!(out.status.code(), Some(1));
    assert!(stderr(&out).contains("not implemented"));
}

#[test]
fn closed_pipe_does_not_abort_the_process() {
    let repo = Repo::new();
    for i in 0..200 {
        repo.commit_file("a.txt", &i.to_string(), &format!("demo: {i}"));
    }
    let mut child = Command::new(env!("CARGO_BIN_EXE_git-panic"))
        .arg("demo:")
        .current_dir(&repo.path)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    // Close our read end immediately, simulating `git-panic demo: | head -0`.
    drop(child.stdout.take());
    let status = child.wait().unwrap();
    assert!(status.code().is_some(), "must exit normally, not by signal");
}
