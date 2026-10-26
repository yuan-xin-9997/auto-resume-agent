# Auto Resume Agent v0.3.0

Adds an optional Codex five-hour window starter, **disabled by default**.

- GUI checkbox and CLI `window-keeper on|off|status`, independent of session recovery.
- After the reported primary 300-minute reset time, even with unused quota, create a new dedicated read-only helper session and send exactly `回复 OK`.
- Recheck all exposed quota windows; unknown availability and weekly/spending blocks wait.
- Durable at-most-once claim per boundary, at least five hours between attempts, no catch-up burst after sleep, and no blind replay after crash/timeout.
- Separate helper RPC client is restricted to its newly created thread and one fixed-message turn; existing user conversations are not used for this feature.
- Five-language controls, status and bilingual documentation. Existing Codex/OpenCode recovery remains available.

This uses one normal model request and attempts to start the next usage period early. It cannot force a quota reset or guarantee a changed server-side reset time. The monitor must remain running. Turning the setting off prevents future submissions; already submitted requests cannot be recalled.

71 automated tests cover timing, safety, default-off behavior, controls and RPC delivery. Live Windows checks verified new-thread creation and prompt acceptance; a provider stream outage prevented verification of a real OK reply. The fixture verifies completion handling. See docs/TESTING.md for limits. The feature remains off after installation/upgrade unless explicitly enabled.

Includes GUI + CLI and SHA-256 files for Windows x64, Linux x64, macOS arm64/x64. Codex/OpenCode are external prerequisites. Prerelease; not signed with a trusted developer certificate/notarized.
