# git-panic

![git-panic: The CLI Emergency Room. Illustrative banner, not a screenshot.](assets/banner.svg)

Find an earlier commit. Give it a branch. Decide what happens next.

A local Git recovery CLI written in Rust. Inspect your HEAD reflog, find an earlier commit, and preserve it on a new branch without switching branches or changing working files.

[Install](#installation) · [Quick start](#quick-start) · [Commands](#command-reference) · [Beginner guide](docs/guide.md) · [Architecture](#architecture) · [Contributing](CONTRIBUTING.md)

## See it in action

![Recorded session: search for a commit after a hard reset, preview recovery, and create a branch without changing the working file.](assets/demo-terminal.svg)

Captured by [scripts/render-demo.sh](scripts/render-demo.sh) in a disposable practice repository. Commands are blue; output is white.

## Why git-panic?

After a confusing reset or rebase, a commit may still exist locally even when your branch no longer points to it. Git's HEAD reflog records where your current Git position has moved. git-panic helps you inspect those entries and give an existing commit a new branch name.

| Feature | What you get |
| :--- | :--- |
| Read-only timeline | Browse HEAD reflog entries and inspect full commit SHAs. |
| Literal search | Filter reflog messages with case-insensitive text. |
| Preview first | Validate a commit and unused branch name without writing changes. |
| Explicit branch creation | Add `--create` only after reviewing the target. Existing branches are never overwritten. |
| JSON output | Use search and recovery from scripts or shell-capable coding assistants. |
| Local Git operations | No checkout, reset, clean, stash, or remote operations. |

This is not an automatic undo button. It preserves existing commits, not edits Git never saved. A recovery branch does not restore working files or back up uncommitted work.

## Installation

You need Git, current stable Rust with Cargo, and a native C compiler with platform build tools for vendored libgit2. OpenSSL development files are not required. The timeline needs an interactive terminal.

```sh
git clone https://github.com/DudeSquad999/git-panic.git
cd git-panic
cargo install --path . --locked
git-panic --help
```

Make sure Cargo's binary directory is on PATH:

| Platform | Directory |
| :--- | :--- |
| Linux / macOS | `~/.cargo/bin` |
| Windows | `%USERPROFILE%\.cargo\bin` |

Alternatively, run `cargo build --release --locked` and use `target/release/git-panic` (`git-panic.exe` on Windows).

The repository includes `Cargo.lock`; `--locked` uses the locked dependency resolution. The source uses `IsTerminal` from Rust 1.70+, but dependencies may require a newer compiler. No minimum supported Rust version or registry publication is verified here.

The previous documented installation and tutorial checks used Linux with rustc 1.99.1. macOS and Windows checks are configured in CI, but were not exercised in that local validation. Builds may need internet access.

## Quick start

After installation, change into the repository you want to inspect, not the git-panic source checkout. Another clone may not have the same local reflog.

### 1. Find a commit

```sh
git-panic                 # Open the read-only timeline
git-panic reset           # Search messages containing "reset"
git-panic "commit: fix"   # Search a phrase containing spaces
```

Search is literal and case-insensitive. It does not interpret natural language or regular expressions. Copy the full 40-character SHA from a result. Quit the timeline before running recovery commands.

### 2. Preview preservation

The following example uses a POSIX shell. Replace the placeholder with an actual commit SHA and choose an unused branch name.

```sh
SHA='<paste-full-40-character-commit-SHA>'
git-panic recover "$SHA" --branch panic/recovered
```

Preview validates the commit and branch name. It writes nothing and does not reserve the name.

### 3. Create the branch when ready

Review the preview before explicitly opting in:

```sh
git-panic recover "$SHA" --branch panic/recovered --create
```

Only the new branch reference is created. HEAD, the index, and working files stay unchanged. Inspecting or integrating files from that branch is a separate decision.

New to recovery? Use the [disposable practice exercise](docs/guide.md#practice-without-risking-your-project) before trying this on an important repository. The [full guide](docs/guide.md) includes PowerShell examples.

## Command reference

| Command | Behavior |
| :--- | :--- |
| `git-panic` or `git-panic tui` | Open the read-only HEAD reflog timeline. |
| `git-panic "query"` | Search HEAD reflog messages for a literal substring. |
| `git-panic --json "query"` | Return search results as JSON. |
| `git-panic recover <SHA> --branch <name>` | Preview preserving a commit on a new branch. |
| `git-panic recover <SHA> --branch <name> --create` | Explicitly create that branch without checking it out. |
| `git-panic recover <SHA> --branch <name> --json` | Return the recovery preview as JSON; also works with `--create`. |
| `git-panic --help` / `git-panic --version` | Show help or version information. |

`recover` requires a full 40-character commit SHA, an available local commit, and a valid unused branch name. Abbreviated SHAs, moving references such as `HEAD@{0}`, non-commit objects, and the branch name `HEAD` are rejected.

`snapshot --before` is reserved but not implemented. It reports failure and is not a recovery option.

### Timeline controls

| Key | Action |
| :--- | :--- |
| Up / Down or `k` / `j` | Select an entry. |
| PageUp / PageDown | Move by ten entries. |
| Home / End | Jump to the newest / oldest entry. |
| `q` or Ctrl-C | Exit. |

The inspector shows the full SHA, reflog position, and action message. It is read-only. `R` does not restore anything. Use literal search instead of the TUI in redirected or captured shell tools. Search output can be piped to tools such as `head` or `grep -m`.

## Scripts and coding assistants

Use the installed CLI through an assistant's shell tool. No plugin, MCP server, model key, or permission bypass is supplied by git-panic.

```sh
git-panic --json reset
git-panic recover "$SHA" --branch panic/recovered --json
```

Search JSON includes `tool`, `query`, `match_count`, and `matches`. Each match contains `index`, `oid`, and `message`. Recovery JSON includes `tool`, `action`, `created`, `commit`, and `branch`.

- A completed search exits 0 even with no matches. Check `match_count`.
- Errors use human-readable stderr and a nonzero exit code.
- JSON is available for search and recovery, not the interactive timeline.
- The documented JSON shape is stable within a version. Check `git-panic --version` before relying on it across releases.
- Confirm the repository and target commit, review the preview, and ask for human approval before adding `--create`.
- Review what shell output a cloud-backed assistant sends to its provider. A local CLI does not make the assistant session offline.

See the [AI-assistant guide and copy-paste task](docs/guide.md#use-with-claude-code-or-another-shell-capable-coding-assistant). Do not parse the default human-readable output in unattended tools.

[AGENTS.md](AGENTS.md) guides assistants editing this project; [CLAUDE.md](CLAUDE.md) imports it for Claude Code. Installing git-panic does not install those instructions into other repositories. The documented noninteractive workflow was previously verified on Linux; instruction-file loading in an actual assistant session remains unverified.

## Safety and limitations

- Only the local HEAD reflog is searched. There is no stash scanning, other branches' reflog scanning, dangling-object search, or visual diff view.
- Unstored edits, expired reflogs, and pruned objects may be unrecoverable.
- A branch is not a backup of staged or unstaged edits, untracked files, conflict resolutions, or interrupted-operation state. Preserve those separately.
- The app does not check out commits, reset files, clean files, stash changes, or contact remotes.
- Interrupted merges, rebases, cherry-picks, and reverts are not finished or aborted.
- Terminal cleanup is best-effort and cannot be guaranteed after aborts or forced stops.

![Illustrative workflow: inspect a commit, preview its SHA and an unused branch, then explicitly create the branch.](assets/readme/workflow.svg)

This workflow image is a command guide, not captured output. The recorded terminal session appears near the top of this README.

## Troubleshooting

| Symptom | What to check |
| :--- | :--- |
| Command not found | Confirm Cargo's binary directory is on PATH in the terminal or assistant environment actually running the command. |
| No Git repository found | Run inside the repository you want to inspect. |
| No matching entries | Try a shorter literal fragment such as `reset` or `commit`. |
| No local HEAD reflog entries | Check the repository and clone. Its reflog may be empty, disabled, or expired; changing the query cannot create entries. |
| Commit unavailable | Verify the full SHA and clone. The object may have been pruned or may not be a commit. |
| Branch already exists | Choose a different name. Existing branches are never overwritten. |
| TUI needs an interactive terminal | Use literal search or JSON in captured or redirected tools. |
| Terminal looks wrong after a forced stop | On POSIX systems, try `stty sane`, then `reset`. |

Read the [troubleshooting guide](docs/guide.md#when-something-fails) for more detail.

## Architecture

[![Architecture diagram of dudesquad999/git-panic](https://gitdiagram.com/dudesquad999/git-panic/diagram.png)](https://gitdiagram.com/dudesquad999/git-panic?utm_source=readme&utm_medium=picture)

[![Architecture diagram](https://gitdiagram.com/diagram-badge.svg)](https://gitdiagram.com/dudesquad999/git-panic?utm_source=readme&utm_medium=badge)

<details>
<summary>View the Mermaid architecture diagram</summary>

```mermaid
%% Generated by https://gitdiagram.com/dudesquad999/git-panic
flowchart TD

subgraph group_interface["CLI interfaces"]
  node_cli["Command dispatch<br/>[main.rs]"]
  node_tui["Timeline inspector<br/>[main.rs]"]
  node_json["JSON responses<br/>[main.rs]"]
end

subgraph group_discovery["Commit discovery"]
  node_search["Literal search<br/>[main.rs]"]
  node_reflog["HEAD reflog<br/>[main.rs]"]
  node_localgit[("Local Git repository")]
end

subgraph group_preservation["Commit preservation"]
  node_recover["Recovery preview<br/>[main.rs]"]
  node_branch["Branch creation<br/>[main.rs]"]
end

node_developer(("Developer / assistant"))

node_developer -->|"invokes"| node_cli
node_cli -->|"reads"| node_reflog
node_localgit -->|"provides entries"| node_reflog
node_cli -->|"routes query"| node_search
node_search -->|"filters entries"| node_reflog
node_cli -->|"opens timeline"| node_tui
node_cli -->|"routes request"| node_recover
node_recover -->|"validates commit"| node_localgit
node_recover -->|"creates on opt-in"| node_branch
node_search -->|"formats results"| node_json
node_recover -->|"formats response"| node_json

click node_cli "https://github.com/dudesquad999/git-panic/blob/main/src/main.rs"
click node_search "https://github.com/dudesquad999/git-panic/blob/main/src/main.rs"
click node_reflog "https://github.com/dudesquad999/git-panic/blob/main/src/main.rs"
click node_tui "https://github.com/dudesquad999/git-panic/blob/main/src/main.rs"
click node_json "https://github.com/dudesquad999/git-panic/blob/main/src/main.rs"
click node_recover "https://github.com/dudesquad999/git-panic/blob/main/src/main.rs"
click node_branch "https://github.com/dudesquad999/git-panic/blob/main/src/main.rs"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_cli,node_tui,node_json toneBlue
class node_search,node_reflog,node_localgit toneAmber
class node_recover,node_branch toneMint
class node_developer toneIndigo
```

</details>

Generated with [GitDiagram](https://gitdiagram.com/dudesquad999/git-panic).

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) for development checks and validation guidance. See [SECURITY.md](SECURITY.md) for the project's security policy.

For bugs and ideas, [open an issue](https://github.com/DudeSquad999/git-panic/issues) with the command, version, and behavior you observed. Remove credentials, private paths, and sensitive repository content before sharing logs.

No blanket installation, security-audit, release-readiness, or AI compatibility guarantee is made.

## Background

The project grew out of the maintainer's recovery experience while building [Prism AI](https://github.com/DudeSquad999/Prism-Ai).

## Licensing status

The manifest declares MIT, but the repository currently has no `LICENSE` file. The maintainer needs to resolve the missing file before users rely on distribution terms.
