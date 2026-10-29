# Release checklist

This checklist prepares a reviewable local release. It does not authorize
publishing, deploying, changing repository visibility, or rotating credentials.
A maintainer must explicitly approve those external actions.

## Source and metadata

- [ ] `pyproject.toml` and `auto_resume_agent.__version__` match.
- [ ] README archive examples, release notes, test evidence, and
      `docs/COMPATIBILITY.md` use the same version and package names.
- [ ] `python -m pytest -q` passes.
- [ ] Synthetic protocol fixtures still match the documented baselines; no real
      conversation, path, account identifier, token, or credential is present.
- [ ] `LICENSE`, `THIRD_PARTY_NOTICES.md`, `licenses/GPL-3.0.txt`,
      `licenses/LGPL-3.0.txt`, and the packaged Python/PySide/PyInstaller license
      files are present in the archive.

## Build and smoke checks

```sh
python scripts/build.py
dist/auto-resume-agent/auto-resume-agent --version   # path varies by OS
dist/AutoResumeAgent/AutoResumeAgent --smoke-test    # offscreen GUI
```

- [ ] Build on each target OS/architecture, or rely on the four-architecture CI
      matrix (Windows x64, Linux x64, macOS arm64, macOS x64).
- [ ] Verify the adjacent `.sha256` file.
- [ ] Inspect the archive for `LICENSE`, `THIRD_PARTY_NOTICES.md`, `licenses/`,
      the CLI/GUI executables, and the platform installer.
- [ ] Record the result as **packaged startup**, not as a real recovery.

## Signing and external acceptance

- [ ] State clearly that artifacts are **unsigned and not notarized** unless a
      maintainer supplied a certificate and completed
      [SIGNING.md](SIGNING.md).
- [ ] Do not commit certificates, private keys, notarization credentials, or
      signing passwords.
- [ ] Perform real Codex/OpenCode acceptance separately with synthetic sessions
      and an isolated state directory. Do not use a personal conversation.
- [ ] Confirm the private security reporting channel in [SECURITY.md](../SECURITY.md).
      If it is not configured, keep that item as a release blocker.
- [ ] Obtain maintainer approval before creating a tag, publishing a release, or
      deploying to a user's machine.

## Evidence to publish

State the version, commit, OS/architecture, test command, packaged startup
result, and what was **not** verified. Keep simulated tests, packaged startup,
and real-platform recovery in separate rows, as in
[COMPATIBILITY.md](COMPATIBILITY.md).
