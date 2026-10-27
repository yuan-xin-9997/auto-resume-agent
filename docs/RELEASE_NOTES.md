# Auto Resume Agent v0.4.3

Fix Codex five-hour helper connectivity: an explicit HTTP(S) proxy can now be configured in Settings or with --codex-proxy. It is inherited by both the monitor and its separate owned-thread helper without changing global environment or Codex configuration. Invalid URLs and embedded credentials are rejected; blank inherits the process environment.

The helper completion deadline is extended from 45 to 150 seconds so a slow stream/reconnect is not interrupted prematurely. Existing durable claims and no-blind-replay behavior remain intact. Existing failed/uncertain windows are not resent.

82 automated tests pass, including proxy validation, child environment isolation and propagation to the helper. Live Windows investigation verified a newly created helper replying exactly OK through the configured local proxy. Overnight missed-boundary investigation also confirmed system sleep; the monitor cannot run while the computer is asleep or off.

Includes native GUI/CLI bundles and SHA-256 checksums for Windows x64, Linux x64 and macOS arm64/x64. Prerelease; unsigned and not notarized.
