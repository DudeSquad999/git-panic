## Summary

Explain the problem and why this change is needed.

Related issue: <!-- Add a link, or write "None". -->

## Changes

-
-

## Validation

List the exact commands run and their results.
Mark checks you could not run; do not imply they passed.

- [ ] Formatting checked.
- [ ] Tests run.
- [ ] Clippy run.
- [ ] Release build checked.
- [ ] Documentation and help reviewed.

Commands and results:

<!-- Paste concise results, not sensitive repository data. -->

## Safety Review

For documentation-only changes, mark this section not applicable.

- [ ] Search and preview remain read-only.
- [ ] Branch creation still requires --create.
- [ ] Existing branches are never overwritten.
- [ ] No implicit checkout, reset, clean, stash, or remote operations.
- [ ] HEAD, index, and working files remain unchanged during recovery.
- [ ] Tests use disposable repositories.

## Compatibility

Describe changes to CLI arguments, JSON output, supported Rust version,
dependencies, or platform behavior.

Write "None" if unchanged.

## Documentation and Examples

Describe documentation updates or explain why none are needed.

## Remaining Limitations

List known issues, skipped checks, and follow-up work.

## Contributor Confirmation

- [ ] I removed secrets and private repository content.
- [ ] I kept this pull request focused.
- [ ] I reviewed CONTRIBUTING.md.
