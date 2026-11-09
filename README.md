# git-panic

![git-panic: The CLI Emergency Room, with a dark-grid background, red-orange title, and illustrative terminal commands.](assets/banner.svg)

Find an earlier commit. Give it a branch. Decide what happens next.

A local Git recovery helper for developers and shell-capable coding assistants.
The banner is illustrative artwork, not a screenshot.

[Beginner and AI-assistant guide](docs/guide.md) · [Install](#install) · [Quick start](#quick-start) · [Limits](#know-the-limits) · [Contributing](CONTRIBUTING.md)

## How it works, in plain English

Git keeps commits: saved snapshots of tracked files. Its local reflog records
where HEAD, your current Git position, has moved. After a confusing reset or
rebase, a commit you need may still be stored locally even if your current
branch no longer points to it.

git-panic helps you find that commit and give it a new branch name. Creating a
branch does not switch HEAD or replace the files in your working folder. It is
not an automatic undo button and cannot promise recovery of edits Git never saved.

New to Git recovery? Start with the [disposable practice exercise](docs/guide.md#practice-without-risking-your-project).
It teaches the difference between preserving a commit and restoring working files.

## Install

Prerequisites: Git, current stable Rust with Cargo, and a native C compiler with
platform build tools for git2/libgit2. The TUI requires an interactive terminal.

```sh
git clone https://github.com/DudeSquad999/git-panic.git
cd git-panic
cargo install --path .
git-panic --help
```

Put Cargo's binary directory on PATH (`~/.cargo/bin`, or
`%USERPROFILE%\.cargo\bin` on Windows). Alternatively build with
`cargo build --release` and use `target/release/git-panic` (`git-panic.exe` on Windows).
The source uses IsTerminal (Rust 1.70+), but dependency requirements may be newer;
no minimum supported version or registry publication is verified here.

After installation, run the command inside the repository you want to inspect,
not the git-panic source checkout. Another clone may lack the older local reflogs.

## Quick start

```sh
git-panic                 # read-only timeline for a human
git-panic tui             # same timeline
git-panic reset           # messages containing the literal substring "reset"
git-panic "commit: fix"   # quote a search fragment containing spaces
```

Up/Down selects an entry; q or Ctrl-C exits. The inspector shows the full SHA,
reflog position and action message. R is not a restoration shortcut. Search is
case-insensitive literal matching, not AI interpretation or regex. No matches
produces a message but still exits successfully. Use search in captured shell tools.

## Preview, then preserve

![Illustrative recovery workflow: inspect a commit, preview its full SHA and an unused branch, then explicitly opt into branch creation.](assets/readme/workflow.svg)

The image is a command guide, not captured output. Copy a full 40-character SHA
from actual history, quit the TUI if using it, and choose an unused branch name:

```sh
SHA='<paste-full-40-character-commit-SHA>'
git-panic recover "$SHA" --branch panic/recovered
# Review the preview before explicitly creating the branch:
git-panic recover "$SHA" --branch panic/recovered --create
```

This example uses a POSIX shell; the placeholder is not a real SHA. See the
[guide](docs/guide.md) for PowerShell and a complete practice exercise.
Preview writes nothing. Invalid names, existing branches and unavailable/non-commit
objects fail. Preview does not reserve a name. Creation never force-updates an
existing branch and does not check out the commit. Integrating files is a separate decision.

## Use with Claude Code and other coding assistants

Use the installed CLI through the assistant's shell tool. Prefer literal search
and recover preview, not the interactive TUI. No plugin, MCP server, model key,
or automatic permission bypass is supplied by git-panic.

The [AI-assistant guide and copy-paste task](docs/guide.md#use-with-claude-code-or-another-shell-capable-coding-assistant)
show how to confirm the target repository, inspect candidates and stop for human
approval before branch creation. They also explain cloud-output privacy and why
human-readable CLI output is not a stable machine API.

[AGENTS.md](AGENTS.md) guides assistants editing this project;
[CLAUDE.md](CLAUDE.md) imports it for Claude Code. Installing git-panic does not
install those instructions into your other projects. Assistant sessions and
instruction loading have not been tested in the editing environment.

## Know the limits

- Only the local HEAD reflog is searched. No stash scanning, other branches'
  reflog scanning, dangling-object search or visual diff view is implemented.
- Unstored edits, expired reflogs and pruned objects may be unrecoverable.
- A branch is not a backup of staged/unstaged edits, untracked files, conflict
  resolutions or interrupted-operation state. Preserve those separately.
- No checkout, reset, clean, stash or remote operation is invoked by the app.
  Interrupted merges/rebases/cherry-picks/reverts are not finished or aborted.
- snapshot --before is reserved but unimplemented and reports failure.
- Terminal cleanup is best-effort, not guaranteed after aborts or forced stops.
- Local application execution does not make a cloud-backed AI session offline.
  Review what output your assistant sends to its provider. Builds may use the network.

## Troubleshooting and development

Command not found? Check PATH in the actual terminal or assistant environment.
No repository? Check the working directory. No matches? Try a shorter literal
fragment. Commit unavailable? Verify the full SHA and clone. Branch exists? Choose
a different name; do not force-update it. A redirected TUI needs an interactive
terminal, so use search instead. On POSIX systems, try stty sane then reset if a
forced stop leaves the terminal altered.

Read the [full guide](docs/guide.md#when-something-fails) and
[CONTRIBUTING.md](CONTRIBUTING.md) for checks and remaining validation. No blanket
installation, security-audit, release-readiness or AI compatibility guarantee is made.

The project grew out of the maintainer's recovery experience while building
[Prism-AI](https://github.com/DudeSquad999/Prism-Ai).

## Licensing status

The manifest declares MIT, but the inspected repository has no LICENSE file.
The declaration is preserved without inventing a holder or license text. The
maintainer needs to resolve the missing file before users rely on distribution terms.
