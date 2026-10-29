# Security policy

## Supported versions

Security fixes are prepared for the latest `0.5.x` source line. Older releases
may not receive fixes; upgrade to the latest published version when possible.

## Reporting a vulnerability

Do **not** open a public issue for a vulnerability, and do not include access
tokens, API keys, passwords, private conversation text, or unredacted state
databases in any report.

**Private reporting channel status:** this repository does not publish a private
security email address, and private GitHub vulnerability reporting has not been
verified as enabled. This is a release blocker for a public release: maintainers
must confirm or enable GitHub private vulnerability reporting (repository
**Settings → Code security**) and update this file before announcing a release.
If the repository's **Security → Report a vulnerability** form is available, use
that channel. Otherwise, do not publish exploit details or secrets publicly;
contact the maintainer through an already-established private project channel.

No email address is invented here. Do not send reports to an address that is not
listed in this repository.

## Useful report contents

- Affected version and platform.
- Whether the issue affects Codex, OpenCode, packaging, or local state.
- Minimal reproduction steps using synthetic sessions and an isolated state
  directory.
- Impact and any suggested mitigation.
- Whether a credential or real conversation may have been exposed. Revoke the
  credential through its provider; do not send it to the project.

## Scope

In scope: exact-session delivery, state/lock handling, compatibility checks,
credential handling, archive/installer behavior, and local privacy boundaries.
Out of scope: vulnerabilities in Codex, OpenCode, Qt/PySide6, or a provider API
that this project does not control; report those upstream as well.
