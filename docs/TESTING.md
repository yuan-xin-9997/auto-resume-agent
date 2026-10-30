# Verification record

## v0.5.3 — compatibility guardrails and release preparation (2026-10-28)

- 123 automated tests pass on the development Windows 11 host. The suite uses
  synthetic sessions, deterministic quota/error replies, temporary state
  directories and an isolated loopback OpenCode fixture. It does not read a real
  conversation or send a continuation to a real session.
- New regressions cover: an unreadable quota window not authorizing another
  window's reset; a latest-turn change between observation and claim; explicit
  missing-method/protocol/response-shape errors; all-send blocking after an
  incompatibility; pause and explicit cancel after a durable claim; OpenCode
  billing denials supplied as objects, unstructured 429 bodies, changed status
  shapes, and missing permission/question routes.
- Synthetic sanitized fixtures for Codex CLI `0.163.0` and OpenCode `1.19.3` are
  in `tests/fixtures/protocol/`. They are shape samples, not captured user data.
  `tests/test_release_metadata.py` keeps the package version, archive names,
  release notes, compatibility matrix and test evidence aligned.
- Local Windows x64 packaging passed on 2026-10-28: `python scripts/build.py`
  produced `AutoResumeAgent-v0.5.3-windows-x64.zip`; the bundled CLI reported
  `0.5.3`; the bundled GUI passed `--smoke-test` with
  `QT_QPA_PLATFORM=offscreen`; the archive contained the license, notices,
  bundled license directory, CLI/GUI executables and installer; and the adjacent
  `.sha256` matched. This is **packaged startup**, not a real recovery. The build
  script now adds Conda's `Library/bin` to the Windows DLL search path so native
  dependencies such as SQLite are included.
- Evidence levels are recorded separately in
  [COMPATIBILITY.md](COMPATIBILITY.md): simulated tests, packaged startup, and
  real-platform recovery are not interchangeable. This change did not perform a
  new real Codex/OpenCode recovery, production quota exhaustion, code signing,
  or notarization. The v0.5.3 prerelease is built and published by CI; the
  historical real-platform checks below remain the only real-recovery evidence.

## v0.3.0 — optional Codex window starter (2026-10-26)

- Default-off GUI checkbox and CLI on/off/status; independent of recovery and scoped by CODEX_HOME.
- 71 tests include unused allowance at expiry, two-second grace, deadline refresh, a server snapshot advancing at the boundary, weekly/unknown quota blocks, unsupported window shapes, sleep/wake catch-up, five-hour spacing, duplicate-instance locking, disable/re-enable, durable crash intent, cancellation before submit and exact fixed-message/owned-thread RPC checks.
- The RPC fixture verifies creation of a new read-only helper thread, exactly one `回复 OK` turn, and verified OK completion. The general monitor client still rejects turn/start; only the separate helper client can start its own thread's fixed turn.
- Live Windows 11 / Codex CLI 0.163.0 checks created dedicated helper sessions and the server accepted the exact prompt. The model stream repeatedly reported responseStreamDisconnected, so a real OK reply was **not** verified; no successful quota-window shift is claimed. Timeout is recorded as uncertain and never automatically replayed. Existing user sessions were not modified.
- A five-hour real-time soak and provider-side changes to usage-window anchoring are not proven by simulated clocks. The request follows reported metadata and cannot force account reset behavior.
- Release CI tests/builds native Windows x64, Linux x64, macOS arm64 and macOS x64, with frozen GUI/CLI startup checks.

## v0.2.0 — OpenCode support (2026-10-26)

- Windows 11: OpenCode 1.19.3 real HTTP health/session API checks passed.
- An isolated real OpenCode server imported a synthetic failed session. Auto Resume Agent detected the retryable failure, posted to the same session, retained the original provider/model/agent, and a local fixture provider completed the continuation. Exactly one additional user message was observed. No production provider credentials or quota were used.
- `scripts/opencode_smoke.py --executable /path/to/opencode` reproduces this test using temporary XDG data/config roots, denied tool permissions and a loopback fixture provider.
- 53 automated tests cover Codex regressions and OpenCode HTTP acceptance, Retry-After, preserved model/agent/variant/tool/system settings, busy/native-retry exclusion, permissions/questions, auth/billing/cancellation exclusion, child/archive/revert exclusion, separate state roots, ambiguous delivery and five-language GUI agent switching.
- Native GUI/CLI build and startup tests run on all four release architectures. OpenCode's provider remaining quota is not exposed by its public API and is correctly shown as unknown. Tests do not prove quota availability with every third-party provider.
- Existing v0.1.0 platform checks below remain historical evidence; new release checks are tied to the v0.2.0 workflow.

## v0.1.0 historical verification


Version: 0.1.0. Date: 2026-10-26 (Asia/Shanghai).

Target compatibility is distinct from tests completed. This prerelease does not claim every target platform has passed a full interactive Codex failure-and-recovery test.

| Environment | Verification |
| --- | --- |
| Windows 11 x64, build 26300 | 28 automated tests; real Codex CLI 0.163.0 usage and thread metadata; native GUI language/navigation checks; packaged CLI doctor; repaired frozen GUI continuously reads real quota and lists sessions |
| Windows 10 1809+ | Target based on Qt 6.8 runtime support; no physical Windows 10 test |
| Ubuntu 24.04.5 x64 | 28 tests on the remote host; Qt X11 window/event loop under Xvfb; frozen CLI and frozen X11 GUI startup passed |
| Ubuntu 26.04.1 x64 | Ubuntu Docker image: the Ubuntu 24-built frozen CLI and Qt offscreen GUI passed; no physical Ubuntu 26 desktop/Wayland test |
| macOS 27.0.1 arm64 | 28 tests on MacBook; native Cocoa window/event loop and five language selections; frozen CLI and frozen Cocoa GUI startup passed |
| macOS Intel | CI build and tests; no physical macOS 27 Intel machine |

## Automated recovery cases

Tests use deterministic quota and history replies. They cover exact UUID submission, observe mode, latest exhausted reset across multiple windows, wake after reset, stale quota, newer user turns, cancellation, terminal/unknown errors, durable crash intent, ambiguous delivery, process exclusion, five-per-hour budget, invalid/non-finite quota data, privacy allowlists, RPC method allowlists and five-language GUI controls.

These simulations do not prove production OpenAI quota exhaustion or delivery to an open desktop conversation. Real usage exhaustion was not deliberately caused, and no ongoing personal conversation was modified for testing.

GitHub Actions builds and tests native Windows x64, Ubuntu x64 and macOS arm64/x64 binaries. [Successful build run](https://github.com/yuan-xin-9997/auto-resume-agent/actions/runs/40247613507) includes 28 tests per platform and frozen GUI/CLI startup checks. A release tag rebuilds the exact tagged source separately.

Ubuntu 24 native startup initially exposed a missing `libxcb-cursor0`; installing the documented dependency fixed it. CI also installs `libegl1` explicitly. See `scripts/ubuntu26-smoke.sh` for the container check. Windows GUI integration additionally exercises external Codex launch; source/CLI tests alone do not cover that boundary.

The Windows frozen GUI initially disconnected while launching external Codex. The adapter now restores the external process's library search environment, including PyInstaller's inherited Windows DLL directory. The rebuilt native GUI was verified connected and refreshing real usage; the regression suite checks child environment sanitization. Optional local `ARA_DEBUG_LOG` captures app-server stderr only when explicitly configured.

## Reproduce

```sh
python -m pip install -e '.[gui,build,test]'
python -m pytest -q
auto-resume-agent doctor
auto-resume-agent usage
python scripts/build.py
```

`doctor` reads official app-server methods and does not send a continuation. `check` is different: it may submit if recovery is enabled and selected sessions qualify.

## Known limits

Codex CLI 0.163.0 is the integration baseline. App-server is experimental. Other versions must pass doctor and may require adapter changes. Queued delivery requires an eligible session consumer; closed conversations can stay queued. No safe automatic takeover is implemented. A newer turn is displayed as progression, never as proven delivery of this tool's continuation. Exactly-once execution cannot be promised across the CLI boundary. The monitor cannot coordinate with the reference Windows product; do not enable both on one session.

## v0.4.0 interface and Windows deployment

74 automated tests pass on the development Windows 11 PC. New coverage checks five-language quota labels, checkbox targets independent of row highlighting, select-all/clear, selection preservation by UUID across refresh/reordering, removed rows, aligned headers/cells, and Windows package validation. Screenshots use synthetic sessions only.

Windows release installation uses a fixed per-user directory and preserves the separate SQLite state directory. The local deployment procedure includes SHA-256 verification, an SQLite backup, before/after settings and watched-session comparison, and inspection of the running native GUI version. See [LOCAL_UPDATES.md](LOCAL_UPDATES.md). Other platform compatibility findings above remain unchanged.

## v0.4.2 — rewatch status

75 tests pass on the development Windows 11 PC. The new regression reproduces a waiting recovery cancelled by unwatching, watches the same UUID again, checks the immediate and refreshed Watching status, and verifies that historical cancellation records remain unchanged. This is a status-display fix and does not revive or resend cancelled recovery requests.

## v0.4.3 — window helper connectivity (2026-10-27)

- 82 automated tests pass, including explicit proxy propagation from persisted settings to the separate WindowClient, preservation of the parent's environment, invalid credential/path/scheme/port rejection and existing at-most-once window rules.
- Windows investigation found helper creation at the scheduled boundary followed by an interrupted turn without an OK reply. Passing the local HTTP proxy produced a real new helper thread and an exact OK completion in approximately 12 seconds. The helper wait is now 150 seconds rather than 45.
- System sleep records explain the overnight missed boundary: suspend at 22:24 and resume at 07:01. No local process runs while the PC is asleep. This release does not change OS power settings or claim uninterrupted five-hour periods during sleep.
- Proxy endpoints are installation-specific; no particular proxy port is built into the product. Credentials are rejected rather than persisted in proxy URLs. User conversations and historical ambiguous delivery claims are not replayed.

## v0.4.4 — previously interrupted watched sessions (2026-10-27)

85 tests pass. Regressions cover an explicitly watched latest failure two hours older than the watch, at-most-once delivery after restart, preservation of cancellation when rewatching an old failure, and interrupted queue placeholders not being treated as execution progression. No history scan or unrestricted replacement agent is introduced.

Live investigation found a usage-limit failure approximately 139 seconds before the user added monitoring; the prior 60-second eligibility cutoff excluded it. The corrected engine detected that exact latest failure and queued one continuation to the original UUID. Execution and task completion must be checked separately from queue acceptance.

The real five-hour boundary at 2026-10-27 18:17:38 +08:00 was observed without manual triggering. A durable helper claim was created at 18:17:49.945, thread/read verified the fixed user prompt 回复 OK and an assistant OK in a completed turn, and the next reported reset became 23:17:58. The one-time observation automation was deleted after verification.

## v0.5.0 — default quota-session discovery

99 tests cover default-on Codex discovery while recovery remains paused, automatic watch followed by quota-available recovery exactly once, latest-turn status/error filters, archived/subagent/helper exclusions, bounded batches and pagination, prioritizing updated recent sessions, persistent manual opt-outs and legacy cancelled-session migration, CLI control and five-language GUI control. Discovery failure is isolated from existing monitored-session recovery. OpenCode discovery is deliberately not inferred from generic API failures.

Automatic watching does not prove execution: Codex queue acceptance still depends on a loaded original session, and provider/network errors remain possible. The app still respects recovery pause and durable claims, and does not send to cancelled or unrelated historical turns.


## v0.5.3 — active windows, session search and activity names

124 automated tests pass on the development Windows PC. Regression coverage includes skipping helpers for an already-active server window across restart, sending at its next expired boundary, case-insensitive name/UUID/workspace search, hidden selections excluded from bulk actions, and activity names surviving restart. No real model request was sent to test the new skip logic.
