# Security guidance

## Project status

 git-panic is early-stage software. This project does not currently document a security-support window, a maintained release series, or a guaranteed response or remediation time. Check the current source and dependency advisories before relying on a build.

A clean build, passing tests, or an audit scan does not establish that the software is free of vulnerabilities.

## Reporting a suspected vulnerability

Do not post exploit details, credentials, private Git history, sensitive paths, or affected repository contents in public issues or pull requests.

A dedicated private reporting channel has not been established in this policy. If GitHub's Security tab offers a private "Report a vulnerability" option for this repository, use that option. Its availability must be checked on GitHub; this document does not claim it is enabled.

If no private option is available, you may open a public issue asking only for a private contact method. Do not include the vulnerability details or sensitive attachments in that request. Wait until a private channel is arranged before sending them.

Once a private channel is available, useful report details include:

- The affected commit or tool version and operating system.
- A minimal reproduction using a disposable repository with synthetic data.
- Expected behavior, observed behavior, and the potential impact.
- Relevant dependency advisories, with secrets removed from any logs.

Do not test against repositories or systems you do not have permission to use.

## Git recovery and privacy

A recovery branch preserves an existing commit reference. It is not a backup of uncommitted work. Preserve important files separately before investigating a recovery problem.

 git-panic performs local Git operations, but a cloud-backed coding assistant may send command output to its provider. Review what is shared and do not assume the overall assistant session is offline.
