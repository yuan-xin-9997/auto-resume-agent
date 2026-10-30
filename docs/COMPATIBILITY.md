# Compatibility and verification matrix

This page separates **documented targets**, **integration baselines**, and the
level of evidence behind each claim. A target is not a guarantee; run `doctor`
against the actual agent installation before enabling recovery.

## Documented backends

| Backend | Integration baseline | Adapter surface | Other versions |
| --- | --- | --- | --- |
| Codex CLI | `0.163.0` | Experimental app-server over stdio; `codex queue` for delivery | Run `doctor`. Missing experimental methods or changed response fields block automatic sending until the adapter is updated. |
| OpenCode server | `1.19.3` | HTTP session, status, permission, question and `prompt_async` routes | Run `doctor`. A missing permission/question route or changed response shape blocks automatic sending. |

Codex cloud-only sessions and other agents (Claude Code, Gemini CLI) are not
implemented. OpenCode does not expose a universal remaining-provider-quota API;
its quota is shown as unknown and retryable API errors use bounded backoff.

## Evidence levels

| Level | What it proves | Current evidence |
| --- | --- | --- |
| Simulated protocol and state tests | Adapter parsing, classification, durable claims, pause/cancel races, ambiguous delivery and restart behavior against deterministic replies | `python -m pytest -q`; synthetic fixtures in `tests/fixtures/protocol/` |
| Packaged startup | The frozen CLI and GUI start on the built architecture; bundled licenses are present | GitHub Actions on Windows x64, Linux x64, macOS arm64 and macOS x64; local `python scripts/build.py` and smoke commands |
| Real platform recovery | A real agent accepted and executed a continuation in an isolated session | Historical v0.2.0 OpenCode 1.19.3 check with an isolated server and local fixture provider; historical v0.4.4 Codex queue/helper checks. These are not re-run by the automated suite. |

## v0.5.3 — version consistency

| Item | Value |
| --- | --- |
| Python package version | `0.5.3` (`pyproject.toml`, `auto_resume_agent.__version__`) |
| Windows archive | `AutoResumeAgent-v0.5.3-windows-x64.zip` |
| Linux archive | `AutoResumeAgent-v0.5.3-linux-x64.tar.gz` |
| macOS archives | `AutoResumeAgent-v0.5.3-macos-arm64.tar.gz`, `AutoResumeAgent-v0.5.3-macos-x64.tar.gz` |
| Checksums | Adjacent `.sha256` files |
| Signing | Unsigned and not notarized by default; see [SIGNING.md](SIGNING.md) |

## Target platforms

| Platform | Target | Verification status |
| --- | --- | --- |
| Windows 10 1809+ / 11, x64 | Installer and portable launch | CI build/startup; Windows 11 interactive checks in historical records |
| Ubuntu 24.04 / 26.04, x64 | Tarball and installer | CI build/startup; Ubuntu 24.04 interactive checks in historical records |
| macOS 27, Apple Silicon / Intel | App bundle and installer | CI build/startup for both architectures; arm64 interactive checks in historical records |

## Not verified by this change

- Real quota exhaustion and recovery against a production Codex account.
- OpenCode recovery against a production provider or real provider credentials.
- Versions other than the documented baselines.
- Code signing, Apple notarization, or SmartScreen reputation.
- Exactly-once execution across the Codex CLI boundary; the final read-to-queue
  race remains because the CLI has no expected-turn atomic precondition.
- The delivery command itself: `doctor` never submits, so it does not exercise
  the Codex `queue` command or OpenCode `prompt_async`. A changed delivery
  command fails closed as `uncertain` and is never retried automatically.
- Coordination with other recovery tools or independent state directories.

The automated suite never reads a developer's real conversation and never sends
a continuation to a real session. See [TESTING.md](TESTING.md) for the dated
records and [STATE_DIRECTORY.md](STATE_DIRECTORY.md) for local data handling.
