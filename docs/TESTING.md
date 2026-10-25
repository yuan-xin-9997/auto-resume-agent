# Verification record

Version: 0.1.0. Date: 2026-10-26 (Asia/Shanghai).

Target compatibility is distinct from tests completed. This prerelease does not claim every target platform has passed a full interactive Codex failure-and-recovery test.

| Environment | Verification |
| --- | --- |
| Windows 11 x64, build 26300 | Native Python/Qt tests, real Codex CLI 0.163.0 usage and thread metadata checks; GUI and packaged CLI smoke tests recorded below |
| Windows 10 1809+ | Target based on Qt 6.8 runtime support; no physical Windows 10 test |
| Ubuntu 24.04 x64 | Remote host and CI verification recorded below |
| Ubuntu 26.04 x64 | Forward target; container verification recorded below if available |
| macOS 27.0.1 arm64 | Remote Mac verification recorded below |
| macOS Intel | CI build and tests; no physical macOS 27 Intel machine |

## Automated recovery cases

Tests use deterministic quota and history replies. They cover exact UUID submission, observe mode, latest exhausted reset across multiple windows, wake after reset, stale quota, newer user turns, cancellation, terminal/unknown errors, durable crash intent, ambiguous delivery, process exclusion, five-per-hour budget, invalid/non-finite quota data, privacy allowlists, RPC method allowlists and five-language GUI controls.

These simulations do not prove production OpenAI quota exhaustion or delivery to an open desktop conversation. Real usage exhaustion was not deliberately caused, and no ongoing personal conversation was modified for testing.

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
