# git-panic

![git-panic: The CLI Emergency Room. Illustrative banner, not a screenshot.](assets/banner.svg)

Find an earlier commit. Give it a branch. Decide what happens next.

I'm Aidan, the creator of git-panic and [Prism AI](https://github.com/DudeSquad999/Prism-Ai). I started this project after dealing with Git recovery while building Prism. git-panic is a local Git recovery CLI written in Rust. It helps you find an earlier commit and preserve it on a new branch without switching branches or changing working files.

[Install](#installation) · [Quick start](#quick-start) · [Commands](#command-reference) · [Beginner guide](docs/guide.md) · [Architecture](#architecture) · [Prism AI](#my-other-project-prism-ai) · [License](LICENSE)

## Why I built it# git-panic

Find the commit. Preserve it. Decide what happens next.

A local Git recovery CLI for browsing reflogs and preserving available commits
on new branches—without switching branches or changing your working files.

[![Build](https://github.com/DudeSquad999/git-panic/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/DudeSquad999/git-panic/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Package version: 0.1.0](https://img.shields.io/badge/package_version-0.1.0-informational.svg)](Cargo.toml)

[Quick start](#quick-start) ·
[Installation](#installation) ·
[Commands](#commands) ·
[User guide](docs/guide.md) ·
[Contributing](CONTRIBUTING.md)

> Early-stage software. git-panic preserves available commits; it cannot recover
> edits Git never stored. It is not an automatic undo button or a backup tool.

## Why This Project?

After a reset or rebase, a commit may still exist locally even when your branch
no longer points to it. Finding that commit under pressure can be confusing.

git-panic provides a focused workflow:

1. Inspect or search the local HEAD reflog.
2. Review the full commit SHA.
3. Preview creating a recovery branch.
4. Explicitly create that branch when ready.

Search and preview are read-only. Creating a recovery branch does not switch
branches or change HEAD, the index, or working files.

## Features

- 🔎 Literal search — Find reflog messages using case-insensitive text.
- 🖥️ Read-only timeline — Browse entries in an interactive terminal.
- 👀 Preview first — Validate the commit and branch name before writing.
- 🌿 Explicit preservation — Create a new branch only with `--create`.
- 🧾 JSON output — Use search and recovery in scripts.
- 🔒 Local operations — No application API keys or remote Git operations.
- 🛡️ Narrow write boundary — Existing branches are never overwritten.

## Demo

![Recorded terminal demonstration](assets/demo-terminal.svg)

Generated in a disposable practice repository using
[scripts/render-demo.sh](scripts/render-demo.sh).

## Installation

### Requirements

- Git.
- Rust 1.88 or newer with Cargo; current stable Rust is recommended.
- A native C compiler and platform build tools for the Git library dependency.
- An interactive terminal for the timeline.

Install Rust using the [official instructions](https://rust-lang.org/tools/install/).

The current Git dependency configuration disables SSH/HTTPS support.
OpenSSL development packages are not required by that configuration.

Builds may need internet access to download dependencies. Installation
instructions should be checked against the revision you are using.

### Linux

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y git build-essential pkg-config
```

Other distributions need equivalent Git, compiler, and build-tool packages.

### macOS

Install Apple's command-line developer tools if needed:

```bash
xcode-select --install
```

Verify that Git is available:

```bash
git --version
```

### Windows

Install:

1. Git for Windows.
2. Rust using the MSVC toolchain.
3. Visual Studio Build Tools with the C++ build tools and Windows SDK.

Use PowerShell for the installation commands below.

### Build and install from source

```bash
git clone https://github.com/DudeSquad999/git-panic.git
cd git-panic
cargo install --path . --locked
git-panic --version
git-panic --help
```

Cargo's executable directory must be on PATH:

| Platform | Directory |
| --- | --- |
| Linux / macOS | `~/.cargo/bin` |
| Windows | `%USERPROFILE%\.cargo\bin` |

To build without installing:

```bash
cargo build --release --locked
```

The executable is `target/release/git-panic`, or
`target\release\git-panic.exe` on Windows.

`--locked` uses the committed dependency resolution. The package version
shown above comes from Cargo.toml; it does not establish a published release.

## Quick Start

Run git-panic inside the repository you want to inspect—not necessarily the
git-panic source checkout.

Reflogs are local: another clone may not contain the same history.

### 1. Inspect or search

```bash
git-panic
git-panic reset
git-panic "commit: fix"
```

The first command opens the timeline. The other commands search reflog
messages.

Search is literal and case-insensitive—not a regular expression or a
natural-language query.

Copy a full 40-character commit SHA from the results. Quit the timeline
before running a recovery command.

### 2. Preview preservation

In the following examples, replace `FULL_40_CHARACTER_SHA` with the actual
commit SHA. Choose an unused branch name.

```bash
git-panic recover FULL_40_CHARACTER_SHA --branch panic/recovered
```

This validates the target and branch name without writing anything.
Preview does not reserve the branch name.

### 3. Create the branch

After reviewing the preview:

```bash
git-panic recover FULL_40_CHARACTER_SHA --branch panic/recovered --create
```

Only the new branch reference is created. There is no checkout, reset, or
working-file restoration.

Inspecting or integrating files from the recovered branch is a separate
decision.

Start with the [disposable practice exercise](docs/guide.md#practice-without-risking-your-project)
before using a recovery workflow on important work.

## Commands

| Command | Purpose |
| --- | --- |
| `git-panic` | Open the read-only timeline. |
| `git-panic tui` | Explicitly open the timeline. |
| `git-panic "query"` | Search local HEAD reflog messages. |
| `git-panic --json "query"` | Return search results as JSON. |
| `git-panic recover <SHA> --branch <name>` | Preview creating a branch. |
| `git-panic recover <SHA> --branch <name> --create` | Create the branch. |
| `git-panic recover <SHA> --branch <name> --json` | Return the preview as JSON. |
| `git-panic --help` | Show command-line help. |
| `git-panic --version` | Show the installed version. |

`<SHA>` and `<name>` denote values you supply; do not paste the angle
brackets into your shell.

JSON also works with explicit branch creation. Errors use human-readable
stderr and a nonzero exit status. A completed search may return no matches;
check `match_count` when using JSON.

Recovery requires an available local commit and a valid unused branch name.
Abbreviated SHAs, moving references such as `HEAD@{0}`, non-commit objects,
and the branch name `HEAD` are rejected.

`snapshot --before` is reserved but not implemented.

### Timeline controls

| Key | Action |
| --- | --- |
| Up / Down or `k` / `j` | Select an entry. |
| PageUp / PageDown | Move by ten entries. |
| Home / End | Jump to the newest / oldest entry. |
| `q` or Ctrl-C | Quit. |

The timeline is read-only. It does not restore files.

## Configuration

git-panic currently has no application-specific environment variables,
configuration file, API keys, or cloud-provider settings.

| Setting | How to control it |
| --- | --- |
| Repository | Run from inside the target repository. |
| Search | Supply a literal positional query. |
| JSON output | Add `--json` to search or recovery. |
| Recovery branch | Supply `--branch <name>`. |
| Branch creation | Explicitly add `--create`. |

Standard Git, terminal, and operating-system behavior may still affect
repository discovery and execution.

## Safety and Limitations

- Only the local HEAD reflog is searched.
- Recovery requires an available local commit and a full 40-character SHA.
- Expired reflogs or pruned objects may make recovery impossible.
- Uncommitted changes and untracked files are not backed up.
- Existing branches are never overwritten.
- The application does not check out, reset, clean, stash, or contact remotes.
- Interrupted Git operations are not completed or aborted.
- Terminal cleanup is best-effort after errors or forced termination.

When using the CLI through a coding assistant, review what repository
output the assistant sends to its provider. A local command does not make
a cloud-backed assistant session offline.

See the [user guide](docs/guide.md) for examples and limitations.

## Troubleshooting

| Problem | Next step |
| --- | --- |
| `git-panic` not found | Check Cargo's executable directory is on PATH. |
| No Git repository found | Run inside the repository you want to inspect. |
| No matching entries | Try a shorter literal query such as `reset`. |
| Empty reflog | Verify the clone and whether local reflogs exist. |
| Commit unavailable | Check the full SHA and whether the object exists. |
| Branch already exists | Choose a different branch name. |
| Interactive terminal required | Use search or JSON instead of the timeline. |

An empty reflog cannot be fixed by changing the search query.

## Development

```bash
cargo fmt --all -- --check
cargo test --all-targets --locked
cargo clippy --all-targets --locked -- -D warnings
cargo build --release --locked
cargo package --locked --list
```

CI is configured for Linux, macOS, and Windows. Consult current workflow
results rather than assuming every revision passes.

## Contributing

Bug reports, documentation improvements, tests, and focused pull requests
are welcome.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and our
[Code of Conduct](CODE_OF_CONDUCT.md).

For suspected vulnerabilities, consult [SECURITY.md](SECURITY.md) before
posting details publicly.

## Related Project

[Prism AI](https://github.com/DudeSquad999/Prism-Ai) is the creator's separate
research and writing project. It is not required to use git-panic.

## License

[MIT](LICENSE). Copyright (c) 2026 DudeSquad999.

Third-party dependencies retain their own licenses and notices.


Git recovery can be confusing when you're trying to figure out what happened to your work. I built git-panic around a small workflow: inspect the history, review a commit, and explicitly choose whether to give it a new branch.

After a reset or rebase, a commit may still exist locally even when your branch no longer points to it. Git's HEAD reflog records where your current Git position has moved. git-panic makes those entries easier to browse and search.

This is not an automatic undo button. It preserves existing commits, not edits Git never saved. A recovery branch does not restore working files or back up uncommitted work.

## See it in action

![Recorded session: find a commit after a hard reset, preview recovery, and create a branch without changing the working file.](assets/demo-terminal.svg)

Captured with [scripts/render-demo.sh](scripts/render-demo.sh) in a disposable practice repository. Commands are blue; output is white. The banner at the top is artwork, not a screenshot.

## What it does

| Feature | What you get |
| :--- | :--- |
| Read-only timeline | Browse HEAD reflog entries and inspect full commit SHAs. |
| Literal search | Filter reflog messages with case-insensitive text. |
| Preview first | Validate a commit and unused branch name without writing changes. |
| Explicit branch creation | Add `--create` after reviewing the target. Existing branches are never overwritten. |
| JSON output | Use search and recovery from scripts or shell-capable coding assistants. |
| Local operations | No checkout, reset, clean, stash, or remote operations. |

![Recovery contract: search and preview are read-only; explicit creation adds a new branch without changing HEAD, the index, or working files. Not a backup of uncommitted work.](assets/readme/recovery-contract.svg)

## Installation

You need Git, Rust 1.88 or newer with Cargo, and a native C compiler with platform build tools for vendored libgit2. Current stable Rust is recommended. OpenSSL development files are not required. The timeline needs an interactive terminal.

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

`Cargo.toml` declares `rust-version = "1.88"`. The merged build-validation notes report successful builds and tests with 1.88.0; 1.87.0 could not resolve the committed dependencies. `Cargo.lock` is committed, and `--locked` uses that dependency resolution. No registry-install command is documented here.

Earlier installation and tutorial checks were documented on Linux with rustc 1.99.1. CI is configured for Linux, macOS, and Windows. Check the latest Actions results before assuming a particular revision passed. Builds may need internet access.

## Quick start

After installation, change into the repository you want to inspect, not the git-panic source checkout. Another clone may not have the same local reflog.

### 1. Find a commit

```sh
git-panic                 # Open the read-only timeline
git-panic reset           # Search messages containing "reset"
git-panic "commit: fix"   # Search a phrase containing spaces
```

Search is literal and case-insensitive, not natural-language interpretation or regular expressions. Copy a full 40-character commit SHA from a result. Quit the timeline before running recovery commands.

### 2. Preview preservation

This example uses a POSIX shell. Replace the placeholder with an actual commit SHA and choose an unused branch name.

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

Start with the [disposable practice exercise](docs/guide.md#practice-without-risking-your-project) if you're new to recovery. The [full guide](docs/guide.md) includes PowerShell examples.

## Command reference

| Command | Behavior |
| :--- | :--- |
| `git-panic` or `git-panic tui` | Open the read-only HEAD reflog timeline. |
| `git-panic "query"` | Search reflog messages for a literal substring. |
| `git-panic --json "query"` | Return search results as JSON. |
| `git-panic recover <SHA> --branch <name>` | Preview preserving a commit on a new branch. |
| `git-panic recover <SHA> --branch <name> --create` | Create that branch without checking it out. |
| `git-panic recover <SHA> --branch <name> --json` | Return the preview as JSON; also works with `--create`. |
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

Use the installed CLI through an assistant's shell tool. git-panic supplies no plugin, MCP server, model key, or permission bypass.

```sh
git-panic --json reset
git-panic recover "$SHA" --branch panic/recovered --json
```

Search JSON includes `tool`, `query`, `match_count`, and `matches`. Each match contains `index`, `oid`, and `message`. Recovery JSON includes `tool`, `action`, `created`, `commit`, and `branch`.

- A completed search exits 0 even with no matches. Check `match_count`.
- Errors use human-readable stderr and a nonzero exit code.
- JSON is available for search and recovery, not the timeline.
- The documented JSON shape is stable within a version. Check `git-panic --version` before relying on it across releases.
- Confirm the repository and commit, review the preview, and ask for human approval before adding `--create`.
- Review what output a cloud-backed assistant sends to its provider. A local CLI does not make the assistant session offline.

See the [AI-assistant guide and copy-paste task](docs/guide.md#use-with-claude-code-or-another-shell-capable-coding-assistant). Don't parse default human-readable output in unattended tools.

[AGENTS.md](AGENTS.md) guides assistants editing this project; [CLAUDE.md](CLAUDE.md) imports it for Claude Code. Installation does not install those instructions into other repositories. The documented noninteractive workflow was previously verified on Linux; instruction-file loading in an actual assistant session remains unverified.

## Safety and limitations

I keep recovery behavior narrow. Read these limits before relying on the tool:

- Only the local HEAD reflog is searched. There is no stash scanning, other branches' reflog scanning, dangling-object search, or visual diff view.
- Unstored edits, expired reflogs, and pruned objects may be unrecoverable.
- A branch is not a backup of staged or unstaged edits, untracked files, conflict resolutions, or interrupted-operation state. Preserve those separately.
- The app does not check out commits, reset files, clean files, stash changes, or contact remotes.
- Interrupted merges, rebases, cherry-picks, and reverts are not finished or aborted.
- Terminal cleanup is best-effort and cannot be guaranteed after aborts or forced stops.

![Illustrative workflow: inspect, preview, and explicitly create a recovery branch.](assets/readme/workflow.svg)

This image is a command guide, not captured output.

## Troubleshooting

| Symptom | What to check |
| :--- | :--- |
| Command not found | Confirm Cargo's binary directory is on PATH in the actual terminal or assistant environment. |
| No Git repository found | Run inside the repository you want to inspect. |
| No matching entries | Try a shorter literal fragment such as `reset` or `commit`. |
| No local HEAD reflog entries | Check the repository and clone. Its reflog may be empty, disabled, or expired. Changing the query cannot create entries. |
| Commit unavailable | Verify the full SHA and clone. The object may have been pruned or may not be a commit. |
| Branch already exists | Choose a different name. Existing branches are never overwritten. |
| TUI needs an interactive terminal | Use literal search or JSON in captured or redirected tools. |
| Terminal looks wrong after a forced stop | On POSIX systems, try `stty sane`, then `reset`. |

See the [troubleshooting guide](docs/guide.md#when-something-fails).

## Architecture

![git-panic architecture: CLI dispatch routes to timeline inspection, literal search, or recovery. Discovery reads the local HEAD reflog. Recovery previews before explicit branch creation; search and recovery support JSON output.](assets/readme/architecture.svg)

The implementation lives in [src/main.rs](src/main.rs). Search and the timeline inspect the local HEAD reflog. Recovery validates an existing commit and an unused branch name, previews without writing, and creates a new branch only when you add `--create`. Search and recovery can return JSON; the interactive timeline cannot.

## My other project: Prism AI

[![Prism AI: research and writing workspace with the original purple prism and colored rays logo.](assets/readme/prism-project.svg)](https://github.com/DudeSquad999/Prism-Ai)

[Prism AI](https://github.com/DudeSquad999/Prism-Ai) is my Windows research and writing workspace. I'm building it to make the path from a research question to a finished document easier to manage, with local or cloud AI and review of AI-proposed edits.

| Application | What it's for |
| :--- | :--- |
| Prism Chat | Research projects, conversations, source material, and Markdown notes. |
| Prism Studio | LaTeX papers and presentations, BibTeX references, and PDF compilation with Tectonic. |

Use local models through Ollama or configure your own API key for Google Gemini, Anthropic, or OpenAI. Chat and Studio need separate configuration. Local inference runs on your computer after setup, but not every feature works offline. Cloud requests send included content to your configured provider.

The [browser workspace](https://dudesquad999.github.io/Prism-Ai/) supports projects, conversations, Markdown drafts, tasks, Perspectives, and project import and export. Connect to Ollama on your computer for live chat; without it, Chat uses labeled sample responses. The browser workspace does not include live web search, citation verification, or document uploads, and does not replace the Windows applications.

Prism is early-stage software. Check important AI-generated claims and citations, review proposed edits, and keep backups. The public repository contains the browser workspace, documentation, automation, and project records, not the complete source for the packaged Windows apps.

Building Prism led me to git-panic. They're separate projects: Prism helps with research and writing; git-panic helps preserve existing Git commits. You don't need Prism to use git-panic, and git-panic isn't a Prism plugin.

[Explore Prism AI](https://github.com/DudeSquad999/Prism-Ai) · [Windows releases](https://github.com/DudeSquad999/Prism-Ai/releases) · [Installation guide](https://github.com/DudeSquad999/Prism-Ai/blob/Main/docs/installation.md) · [Browser workspace](https://dudesquad999.github.io/Prism-Ai/)

## Feedback, contributing, and security

For ordinary bugs or confusing steps, [open an issue](https://github.com/DudeSquad999/git-panic/issues) with the command, version, what you expected, and what happened. Remove credentials, private paths, and sensitive repository content before sharing logs.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for development checks. For a suspected vulnerability, read [SECURITY.md](SECURITY.md) before posting. A dedicated private reporting channel and response-time commitment have not been established in this documentation.

I don't claim a blanket installation, security-audit, release-readiness, or AI compatibility guarantee. The limitations above are part of the documentation, not fine print.

## License

 git-panic is licensed under the [MIT License](LICENSE), matching `license = "MIT"` in `Cargo.toml`.

Copyright (c) 2026 DudeSquad999. Third-party dependencies retain their own licenses and notices.
