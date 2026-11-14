# Contributing to git-panic

Thank you for helping improve git-panic. We welcome reproducible bug reports,
clear documentation, focused fixes, and tests.

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Before You Start

- Search existing issues and pull requests.
- Discuss large features or architectural changes before implementing them.
- Keep each pull request focused on one problem.
- Never use your real project as a destructive recovery test fixture.

For suspected vulnerabilities, read [SECURITY.md](SECURITY.md).
Do not publish credentials, sensitive repository data, or exploit details
in ordinary issues.

## Report a Bug

Include:

- git-panic version or source commit.
- Operating system, terminal, and installation method.
- Exact command, with sensitive values redacted.
- Expected and actual behavior.
- Minimal reproduction steps using a disposable repository.
- Relevant output and exit status.

For build failures, include `rustc --version`, `cargo --version`, and the
first relevant error, not only the final "build failed" message.

Do not upload private repositories or unredacted reflogs.

## Suggest a Feature

Explain:

1. The user problem.
2. Why the current workflow does not solve it.
3. Proposed commands or interactions.
4. Alternatives considered.
5. Effects on safety, compatibility, or repository writes.

A feature request does not imply a commitment to implement it.

## Development Setup

You need Git, Rust, Cargo, rustfmt, Clippy, and native build tools.
See the README for platform prerequisites.

`Cargo.toml` declares Rust 1.88 as the minimum supported version.
Changes that raise this requirement must update the manifest and
documentation explicitly.

```bash
git clone https://github.com/DudeSquad999/git-panic.git
cd git-panic
rustup component add rustfmt clippy
git switch -c fix/short-description
```

Without repository write access, fork the project and clone your fork.

## Required Checks

```bash
cargo fmt --all -- --check
cargo test --all-targets --locked
cargo clippy --all-targets --locked -- -D warnings
cargo build --release --locked
cargo package --locked --list
```

Use `cargo fmt --all` to fix formatting. State which checks passed, failed,
or could not be run. Never describe unexecuted checks as passing.

CI is configured for Linux, macOS, and Windows. Consult the latest Actions
results before claiming a revision passed.

## Coding Standards

- Follow rustfmt and address Clippy warnings.
- Prefer cohesive functions and explicit error handling.
- Add useful context to errors.
- Avoid introducing panics in runtime paths.
- Preserve CLI entry points unless a breaking change is intentional.
- Keep human-readable output separate from machine-readable JSON.
- Update help text and documentation when behavior changes.
- Avoid unrelated formatting, renaming, and dependency changes.

## Git Safety Contract

Preserve these properties:

- Search and preview do not write repository state.
- Recovery previews by default.
- Only `--create` authorizes a new branch reference.
- Existing branches are never overwritten.
- Recovery does not implicitly check out, reset, clean, stash, or contact remotes.
- Branch creation leaves HEAD, the index, and working files unchanged.
- A recovery branch is not a backup of uncommitted edits.

Changes to this contract require explicit design discussion and tests.

## Dependencies

Commit `Cargo.lock` for this CLI application. Use Cargo to update dependency
resolution. Do not hand-edit checksums or resolved dependency entries.

Explain each dependency change. Review transitive changes, minimum Rust
requirements, licenses, and security advisories. Do not suppress an advisory
merely to make a check green, and do not carry historical audit results
forward as current guarantees.

The application uses `git2` without its default SSH/HTTPS features because
git-panic performs no remote operations. `serde_json` supports the documented
JSON output for search and recovery.

## Tests and Manual Validation

Unit tests in `src/main.rs` use disposable libgit2 repositories. Integration
tests in `tests/cli.rs` exercise the compiled binary against throwaway
repositories created with Git. Never run destructive recovery tests in real
worktrees.

Cover, where relevant:

- Empty reflogs and searches with no results.
- Literal, case-insensitive matching.
- Invalid or abbreviated commit IDs.
- Missing and non-commit objects.
- Invalid or existing branch names.
- Preview performing no writes.
- Branch creation preserving HEAD, index, and working files.
- JSON output and error exit status.
- Piped output and terminal cleanup.

On a POSIX platform with Python PTY support:

```bash
cargo build --release --locked
python3 scripts/tui-pty-test.py
```

This test does not substitute for native Windows testing. Remaining manual
scenarios include live resizing, injected terminal errors, interrupted
rebases/cherry-picks/reverts, concurrent branch-name creation, bare
repositories, linked worktrees, and installation examples on each supported
platform. Record exact commands, outcomes, and skipped checks.

## Documentation and Visuals

Keep help, README examples, and implemented behavior aligned. Distinguish
recorded output from illustrative artwork. The workflow SVG is illustrative.
`assets/demo-terminal.svg` is generated by `scripts/render-demo.sh` from a
disposable repository; regenerate it rather than editing captured output by
hand.

Remove credentials, private paths, author identities, and sensitive history
from examples, screenshots, and fixtures. Read [SECURITY.md](SECURITY.md)
before discussing suspected vulnerabilities. Do not promise a reporting
channel, response time, or security support window that has not been
established.

## Compatibility and Licensing

Default, query, and `tui` entry points remain available. `snapshot --before`
is reserved and fails because it is not implemented. `R` is not a restoration
action. Recovery requires a full 40-character SHA-1 commit ID, not an
abbreviated SHA or moving reflog reference.

Use JSON for scripts; default human-readable output is not a stable parsing
interface. Check the tool version when relying on the documented JSON shape.

The project uses the [MIT License](LICENSE), matching `Cargo.toml`. Preserve
its copyright and permission notice and retain applicable third-party license
notices. Do not change licensing terms as part of unrelated fixes.

## Pull Requests

Include:

- The problem and proposed solution.
- A linked issue, if applicable.
- Tests and manual checks performed.
- CLI, JSON, documentation, and compatibility changes.
- Remaining limitations and skipped validation.

Maintainers may request changes or decline proposals outside project scope.
