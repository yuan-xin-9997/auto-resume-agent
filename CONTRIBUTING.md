# Contributing

Thanks for helping improve Auto Resume Agent. Keep changes focused on the
existing Codex and OpenCode adapters; this project deliberately avoids a
generic agent framework, background service, multi-account sync, or GUI rewrite.

## Development setup

Python 3.11 or newer:

```sh
python -m venv .venv
# Activate the virtual environment using your shell's normal command.
python -m pip install -e '.[gui,build,test]'
python -m pytest -q
```

For a headless environment, `python -m pip install -e '.[test]'` is enough for
the CLI and tests. Run `python scripts/build.py` only on the target OS and
architecture.

## Test rules

- Use synthetic sessions, synthetic UUID/session IDs, temporary state
  directories, and fake quota/error replies. Never read a real Codex or
  OpenCode conversation as a fixture.
- Never send a continuation to a real session from a test. Real-platform
  acceptance is a separate, explicitly reviewed step.
- Protocol fixtures live in `tests/fixtures/protocol/`. They must be sanitized:
  no prompts, transcripts, paths, account identifiers, tokens or credentials.
- Preserve the existing safety invariants: observe-only default, exact session
  identity, pause/cancel priority, durable claim before delivery, and no blind
  resend after an ambiguous result.
- Add a regression for every behavior change, including quota-window changes,
  sleep/wake deadlines, latest-turn changes, duplicate instances, backend
  switching, and compatibility failures.

## Compatibility changes

`doctor` is the read-only entry point for checking a new agent version. If a
method disappears or a response field changes, raise an explicit compatibility
error instead of guessing or sending. Update
[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) and the synthetic fixtures when a
documented baseline changes.

## Pull request checklist

- [ ] Tests pass with `python -m pytest -q`.
- [ ] Version, archive names, release notes, and test evidence stay consistent
      (covered by `tests/test_release_metadata.py`).
- [ ] No secrets, real transcripts, personal paths, or generated build artifacts
      are committed.
- [ ] Safety behavior is unchanged or the change is explained with a regression.
- [ ] User-facing documentation is updated in English and Chinese where relevant.
- [ ] `python scripts/build.py` and the bundled `--version` / GUI
      `--smoke-test` commands pass when packaging changes.

Do not create a release tag, publish artifacts, rotate credentials, or change
repository visibility as part of a normal contribution. See
[docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) for the release process.
Security reports follow [SECURITY.md](SECURITY.md), not a public issue.
