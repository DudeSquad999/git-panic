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
first relevant error—not only the final "build failed" message.

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

Cargo.toml declares Rust 1.88 as the minimum supported version.
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

Use `cargo fmt --all` to fix formatting.

State which checks passed, failed, or could not be run.
Never describe unexecuted checks as passing.

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

## Tests

Use temporary repositories and disposable directories.

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

This test does not substitute for native Windows testing.

## Dependencies

Commit Cargo.lock for this CLI application.

Use Cargo to update dependency resolution. Do not hand-edit checksums or
resolved dependency entries.

Explain each dependency change. Review transitive changes, minimum Rust
requirements, licenses, and security advisories.

Do not suppress an advisory merely to make a check green.
Do not carry historical audit results forward as current guarantees.

## Documentation and Visuals

Keep examples consistent with implemented behavior.

Distinguish recorded output from illustrative artwork.
Regenerate the recorded demo using repository scripts.

Remove credentials, private paths, author identities, and sensitive history
from examples and fixtures.

## Pull Requests

Include:

- The problem and proposed solution.
- A linked issue, if applicable.
- Tests and manual checks performed.
- CLI, JSON, documentation, and compatibility changes.
- Remaining limitations and skipped validation.

Maintainers may request changes or decline proposals outside project scope.

## License

Contributions are submitted under the project's MIT License unless a
separate agreement explicitly states otherwise.

Preserve applicable copyright and third-party license notices.
