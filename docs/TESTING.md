# Verification record

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
