# Understand git-panic and use it with coding assistants

[Back to README](../README.md)

## Start here: what can it recover?

Git stores commits: saved snapshots of tracked files. A branch is a name pointing
to a commit. HEAD identifies your current position. A SHA is a commit's ID.
A reflog is a local diary of where a reference such as HEAD has pointed.

If a reset or rebase moved you away from a commit, the old commit may still exist
locally and appear in the reflog. git-panic helps find and name that commit.
It cannot promise recovery of an edit Git never stored or an object already pruned.

```text
local HEAD reflog -> full commit SHA -> preview -> new branch reference
```

Creating that branch does not move HEAD or copy files into your working folder.
That is intentional: inspect the preserved commit before deciding how to integrate
it. A dirty working tree, staged files, or merge conflicts are not backed up by a
branch. Do not let an assistant describe this as an automatic undo button.

## Install in one place; inspect the right repository

Follow the [source installation instructions](../README.md#install).
Then leave the git-panic source checkout and run the installed command inside the
repository whose history you need. Otherwise you inspect git-panic's own history.

```sh
# Run these inside the repository you want to inspect:
git status --short
git-panic reset
```

Search is a literal, case-insensitive substring, not an AI query. Try `reset`,
`rebase`, or part of a message you recognize. No matches is not an error exit.
Only HEAD's local reflog is searched; cloning again does not recreate old local
reflogs. For a human, `git-panic tui` opens the timeline; Up/Down selects and q exits.

## Practice without risking your project

This exercise requires the installed git-panic command and a POSIX shell such as
Bash. It creates a fresh temporary repository, changes only that repository's
configuration, and leaves it for inspection. It uses no reset, clean, or checkout.
Do not substitute your real project directory for the temporary directory.

```sh
DEMO="$(mktemp -d)"
cd "$DEMO"
git init --template=
mkdir no-hooks
git config core.hooksPath "$DEMO/no-hooks"
git config user.name "git-panic demo"
git config user.email "demo@example.invalid"
git config commit.gpgsign false
git config core.autocrlf false

printf 'first version\n' > notes.txt
git add notes.txt
git commit -m "demo: first version"
SHA="$(git rev-parse HEAD)"

printf 'second version\n' > notes.txt
git add notes.txt
git commit -m "demo: second version"

git-panic "demo:"
git-panic recover "$SHA" --branch panic/demo
# Stop and review: preview has not created a branch.
git-panic recover "$SHA" --branch panic/demo --create

git show panic/demo:notes.txt
cat notes.txt
```

If the commands succeed, `git show` should display the first version while `cat`
still displays the second. That demonstrates branch preservation without file
restoration. This is an instructional example, not captured git-panic output.
The Git-only fixture was checked locally; the full application exercise still
needs execution on a Rust-equipped machine. The temporary directory is left intact.

For native PowerShell, use the normal workflow in an existing repository:

```powershell
$sha = '<paste-full-40-character-commit-SHA>'
git-panic recover $sha --branch panic/recovered
# After reviewing the preview:
git-panic recover $sha --branch panic/recovered --create
```

The placeholder is not a real SHA. Use an unused branch name and a commit selected
from actual history, not one invented by an assistant.

## Use with Claude Code or another shell-capable coding assistant

There is no bundled AI plugin, MCP server, API endpoint, or model integration.
The practical connection is a shell tool running the installed CLI in your target
repository. The assistant needs the same binary, PATH, repository access, and local
Git objects you do. It cannot inspect your laptop from a separate cloud environment
unless that environment has access to the relevant repository and its local data.

Prefer literal search and recover preview. Do not launch the interactive TUI from
a captured shell session: a populated TUI needs interactive stdin and stdout.
Current output is human-readable text, not a stable JSON API. Do not build an
unattended parser around it or assume that a successful search means a match exists.

### A task you can paste into Claude Code or another coding assistant

```text
Help me inspect possible Git recovery commits in the repository I identify.
First confirm the repository path, my goal, and that git-panic is installed.
Run git status --short and summarize the state without discarding or stashing work.
Use noninteractive git-panic searches such as reset or rebase; do not use the TUI.
If the searches miss the relevant history, explain the HEAD-reflog limitation.
Do not invent commit IDs. Inspect candidate metadata with git show --no-patch
and explain why a candidate might be relevant; ask me to choose the full SHA.
Preview git-panic recover FULL_SHA --branch UNUSED_NAME without --create.
Show the exact SHA, branch name, preview result, and limits; then stop for approval.
Do not run --create, checkout, reset, clean, stash, merge, rebase, cherry-pick,
push, or any other state-changing Git operation without specific approval.
Do not send private file contents or secrets to a remote service without approval.
```

This is guidance, not enforcement. Keep the assistant's permission prompts and
sandbox controls enabled. No hooks, auto-approval rules, or global settings are
installed by this repository's instruction files.

### Instructions in this project versus your project

The root [AGENTS.md](../AGENTS.md) is for assistants editing git-panic itself.
[CLAUDE.md](../CLAUDE.md) imports that shared guidance for Claude Code. Installing
the binary does not copy either file into your other repositories or change your
assistant's settings. To use git-panic in another project, paste the task above or
add a short, reviewed recovery rule to that project's existing instruction file.
Do not overwrite an existing CLAUDE.md or AGENTS.md just to add this tool.

Claude Code documents project instruction files and @-imports in its
[official memory guide](https://code.claude.com/docs/en/memory). Verify loading in
your installed assistant; do not assume all tools recognize the same file format.
For other agents, explicitly ask them to read the relevant guidance if needed.
Instruction loading and end-to-end assistant sessions have not been tested here.

### Privacy matters

The git-panic application invokes no network operation. That does not make an
AI-assisted session offline: a cloud-backed assistant may send prompts, metadata,
file names, and command output to its provider. Review the assistant's data policy
and permissions before giving it a private repository. Do not paste secrets into
prompts, screenshots, issue reports, or recovery examples.

## Common recovery situations

| Situation | Useful next step | What not to assume |
| --- | --- | --- |
| A reset moved a branch away from a commit | Search `reset`, inspect candidate commits, then preview a new branch. | The reset message alone identifies the desired snapshot. |
| A rebase changed commit IDs | Search `rebase` and inspect metadata around the event. | Every rewritten commit still exists locally. |
| HEAD is detached | Inspect the full SHA and preview naming a commit. | Creating a branch switches you onto it. |
| Merge/rebase/cherry-pick is interrupted | Inspect status, preserve work separately, and stop before additional Git actions. | A recovery branch backs up conflicts or finishes the operation. |
| Only uncommitted edits disappeared | Check your editor's local history or existing backups separately. | A reflog records every edit. |

## When something fails

- Command not found: check Cargo's binary directory on PATH. The assistant's shell
  can have a different environment from your terminal.
- No repository: use the target project's working directory, not the tool checkout.
- No entries/matches: check the clone and search fragment; do not claim success.
- Unavailable commit: confirm the full SHA; an object may have been pruned.
- Branch exists: choose a different name; do not force-update it.
- Need actual file integration: that is a separate, potentially disruptive Git
  operation. Review current work and obtain a specific plan and approval first.
