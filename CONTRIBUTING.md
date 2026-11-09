# Contributing

## Setup and checks

Use current stable Rust with Cargo, rustfmt and Clippy, Git and native build tools.

```sh
cargo fmt --all
cargo fmt --all -- --check
cargo test --all-targets
cargo clippy --all-targets -- -D warnings
cargo build --release
cargo package --list
```

The editing environment had no Cargo, rustc or rustfmt. These Rust checks,
installation and the actual TUI have not been run there. Do not infer success
from authored tests or workflow configuration. The workflow runs tests, Clippy,
release builds and package listing on Linux, macOS and Windows; platform support
remains unverified until results are inspected. Run rustfmt and commit its focused
output before adding a formatting CI gate.

The inspected baseline had no Cargo.lock. Generate, review and commit a binary
lockfile from a trusted dependency resolution, then use --locked checks. Do not
hand-author a lockfile. No resolved dependency vulnerability scan was performed.
Unused serde/serde_json direct dependencies were removed; none were added/upgraded.

## Architecture and safety

The single Rust binary in src/main.rs contains Clap definitions, HEAD reflog
extraction, literal filtering, the Ratatui/Crossterm inspector and branch creation.
Keep this small architecture and dependency footprint unless a concrete need
justifies a change. Recover previews by default; --create opts into a new branch
reference using force=false. Never add implicit checkout, reset, stash or remote
operations. Branch creation itself handles name races without force-overwriting.
It does not preserve uncommitted files, conflict resolutions or operation state.

A terminal guard attempts cleanup after ordinary errors, including partial setup.
The preserved release panic=abort setting, SIGKILL and some terminal failures can
bypass cleanup. Do not advertise universal rollback or restoration guarantees.

## Tests and manual validation

Twelve regression tests are authored, not yet executed in the editing environment.
Fixtures create new repositories in unique OS temporary directories using fixture
identities, and remove them on drop. Never run destructive tests in real worktrees.
Coverage includes parser consistency, legacy parsing, literal search, control
characters, empty logs, reflog extraction, preview, branch-name collisions, bad
objects, and detached HEAD/index/staged/unstaged/untracked preservation.

Before merging, test:

- Normal quit, Ctrl-C, resizing, narrow terminals, long histories and Unicode.
- Cleanup after injected terminal setup, read and draw errors.
- Merge conflicts and interrupted rebase/cherry-pick/revert operations.
- Concurrent name creation, bare repositories and linked worktrees.
- README installation and commands in isolated environments on claimed platforms.

## Documentation and visuals

assets/workflow.svg is original static workflow artwork with an opaque,
high-contrast background and explicit illustrative labeling, not a screenshot.
A real recording requires a compiled app and a disposable demonstration repository.
Record commands, dimensions and the commit used. Never expose secrets or private
history in fixtures, output or recordings. Existing banner/logo assets are retained
but not embedded because they imply unsupported commands or output.

Keep README and help aligned with implementation. Do not add publication, speed,
passing-test or recovery claims without evidence. No private security reporting
route was verified, so this pass does not invent SECURITY.md or response promises.
Do not post secrets or sensitive exploit details publicly.

## Compatibility and licensing

Default/query/tui/snapshot syntax is preserved. Snapshot now fails instead of
falsely succeeding. Search output uses full SHAs and explicit HEAD@{n} labels;
consumers parsing human-readable output may need adjustment. R is still not a
restoration action. The source uses IsTerminal (Rust 1.70+); dependency MSRV has
not been verified. The full-SHA recovery command targets Git SHA-1 commits.

Leave the MIT manifest declaration unchanged. Ask the maintainer to resolve the
missing LICENSE file rather than selecting licensing terms on their behalf.
