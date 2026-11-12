# Compatibility and verification matrix

## v1.1.1 — OpenCode desktop credential refresh

The recovery adapters are unchanged from v1.1.0. For loopback OpenCode 2.x
services, ARA prefers the password in `~/.config/opencode/service.json`,
re-reads it when OpenCode rotates it, and falls back to
`OPENCODE_SERVER_PASSWORD` only for manually started servers or when the file is
stale. Remote URLs still never use local service credentials.

## v1.1.0 — signed auto-updates

The recovery adapters are unchanged from v1.0.0. v1.1.0 adds a separate update
path:

| Install type | Update behaviour |
| --- | --- |
| Windows per-user (`%LOCALAPPDATA%\Programs\AutoResumeAgent`) | Download, verify, swap and restart in place; previous directory retained for rollback |
| Linux per-user (`~/.local/share/auto-resume-agent`) | Same in-place swap and rollback |
| macOS `~/Applications/AutoResumeAgent.app` plus CLI directory | Replace the app bundle and CLI, then relaunch |
| Portable archive | No self-modification; the banner opens the release asset |
| Source checkout | No self-modification |

Update manifests are ECDSA P-256 signed with a key separate from the license
key; archives are verified by SHA-256 and package layout before execution. The
bundles remain **unsigned and not notarized** unless the maintainer supplied
platform signing credentials, so OS-level warnings are unchanged.

## v1.0.0 — paid edition

The v1.0.0 code is the same Codex/OpenCode adapter as v0.5.7 with an added
offline licensing gate. Trial and paid licenses unlock automatic recovery;
monitoring, usage, session listing and `doctor` remain available without a
license. The license gate is enforced in the engine before a recovery claim and
before a Codex window-start request, as well as in the GUI and CLI.

This page separates **documented targets**, **integration baselines**, and the
level of evidence behind each claim. A target is not a guarantee; run `doctor`
against the actual agent installation before enabling recovery.

## Documented backends

| Backend | Integration baseline | Adapter surface | Other versions |
| --- | --- | --- | --- |
| Codex CLI | `0.163.0` | Experimental app-server over stdio; `codex queue` for delivery | Run `doctor`. Missing experimental methods or changed response fields block automatic sending until the adapter is updated. |
| OpenCode server | `1.19.3` (v1) and `2.2.5` (2.x desktop, experimental) | 1.19.x: session, status, permission, question and `prompt_async`. 2.x: `/api/session`, `/api/session/active`, `/api/session/{id}/message`, `/api/session/{id}/prompt`, `/api/permission/request`, `/api/session/{id}/form` and `/api/experimental/usage/limits` | Run `doctor`. A missing required route or changed response shape blocks automatic sending. |

Codex cloud-only sessions and other agents (Claude Code, Gemini CLI) are not
implemented. OpenCode 1.19.x does not expose a universal remaining-provider-quota
API; its quota is shown as unknown. OpenCode 2.x exposes the OpenCode Go/Go Plus
rolling, weekly and monthly allowance and reset times through an experimental
endpoint. Other providers remain unknown.

## OpenCode 2.x support (experimental)

The 2.x adapter auto-detects the `/api` surface after the v1 `/global/health`
probe. It uses Basic authentication from `OPENCODE_SERVER_PASSWORD`, maps 2.x
`provider.*` errors to the existing recovery categories, and reads
`/api/experimental/usage/limits` for the Go/Go Plus allowance. The 2.x prompt
route uses the session's current model, agent and variant and is sent with
`delivery: queue` and `resume: true`. The 2.x API is experimental; a changed
route or shape blocks automatic sending and `doctor` reports it. The 1.19.x
adapter remains available unchanged.

## Evidence levels

| Level | What it proves | Current evidence |
| --- | --- | --- |
| Simulated protocol and state tests | Adapter parsing, classification, durable claims, pause/cancel races, ambiguous delivery and restart behavior against deterministic replies | `python -m pytest -q`; synthetic fixtures in `tests/fixtures/protocol/` |
| Packaged startup | The frozen CLI and GUI start on the built architecture; bundled licenses are present | GitHub Actions on Windows x64, Linux x64, macOS arm64 and macOS x64; local `python scripts/build.py` and smoke commands |
| Real platform recovery | A real agent accepted and executed a continuation in an isolated session | Historical v0.2.0 OpenCode 1.19.3 check with an isolated server and local fixture provider; historical v0.4.4 Codex queue/helper checks; 2026-11-02 OpenCode 2.2.5 synthetic `prompt` delivery in a temporary session, deleted afterward. These are not re-run by the automated suite. |

## v0.5.7 — version consistency

| Item | Value |
| --- | --- |
| Python package version | `0.5.7` (`pyproject.toml`, `auto_resume_agent.__version__`) |
| Windows archive | `AutoResumeAgent-v0.5.7-windows-x64.zip` |
| Linux archive | `AutoResumeAgent-v0.5.7-linux-x64.tar.gz` |
| macOS archives | `AutoResumeAgent-v0.5.7-macos-arm64.tar.gz`, `AutoResumeAgent-v0.5.7-macos-x64.tar.gz` |
| Checksums | Adjacent `.sha256` files |
| Signing | Unsigned and not notarized by default; see [SIGNING.md](SIGNING.md) |

## v0.5.4 — version consistency

| Item | Value |
| --- | --- |
| Python package version | `0.5.4` (`pyproject.toml`, `auto_resume_agent.__version__`) |
| Windows archive | `AutoResumeAgent-v0.5.4-windows-x64.zip` |
| Linux archive | `AutoResumeAgent-v0.5.4-linux-x64.tar.gz` |
| macOS archives | `AutoResumeAgent-v0.5.4-macos-arm64.tar.gz`, `AutoResumeAgent-v0.5.4-macos-x64.tar.gz` |
| Checksums | Adjacent `.sha256` files |
| Signing | Unsigned and not notarized by default; see [SIGNING.md](SIGNING.md) |

## Target platforms

| Platform | Target | Verification status |
| --- | --- | --- |
| Windows 10 1809+ / 11, x64 | Installer and portable launch | CI build/startup; Windows 11 interactive checks in historical records |
| Ubuntu 24.04 / 26.04, x64 | Tarball and installer | CI build/startup; Ubuntu 24.04 interactive checks in historical records |
| macOS 27 | Apple Silicon arm64 in 1.1.0; Intel x64 remains on 1.0.0 | arm64 1.1.0 build/startup verified; Intel x64 1.0.0 archive remains available |

## Not verified by this change

- Real quota exhaustion and recovery against a production Codex account.
- OpenCode recovery against a production quota-exhausted session or a forced
  Go/Go Plus reset; the 2.2.5 synthetic delivery used a real local service but
  did not force quota exhaustion.
- Versions other than the documented baselines.
- Code signing, Apple notarization, or SmartScreen reputation.
- Exactly-once execution across the Codex CLI boundary; the final read-to-queue
  race remains because the CLI has no expected-turn atomic precondition.
- The delivery command itself: `doctor` never submits, so it does not exercise
  the Codex `queue` command, OpenCode 1.19.x `prompt_async`, or 2.x `prompt`.
  A manual synthetic 2.x delivery is recorded in TESTING.md. A changed delivery
  command fails closed as `uncertain` and is never retried automatically.
- Coordination with other recovery tools or independent state directories.

The automated suite never reads a developer's real conversation and never sends
a continuation to a real session. See [TESTING.md](TESTING.md) for the dated
records and [STATE_DIRECTORY.md](STATE_DIRECTORY.md) for local data handling.
