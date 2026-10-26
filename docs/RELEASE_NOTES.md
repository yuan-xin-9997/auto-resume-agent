# Auto Resume Agent v0.2.0

Adds OpenCode support alongside Codex across GUI and CLI.

- Agent selector, OpenCode server URL/workspace settings, and CLI --agent opencode.
- Exact-session recovery of known retryable API errors, respecting Retry-After and the original provider/model/agent/variant and per-message tool/system/format settings.
- Avoids busy/native-retrying sessions, permission/question waits, child/archived sessions and staged reverts.
- Separate state per server/workspace; ambiguous submissions are never automatically repeated.
- Five languages updated; existing Codex state retained.

OpenCode does not expose universal provider remaining quota. Its quota card correctly shows Unknown; bounded retries do not prove quota availability. HTTP acceptance does not prove execution. Basic auth uses environment variables. HTTP is restricted to loopback; remote servers require HTTPS.

Verified with real OpenCode 1.19.3 on Windows 11 and an isolated local fixture model: an imported failed session resumed and completed, with no duplicate user message and no real provider quota consumed. Automated tests and native builds cover all four release architectures. See docs/TESTING.md for scope.

Includes native GUI + CLI archives and SHA-256 files for Windows x64, Linux x64, macOS arm64/x64. Agent software is not bundled. Prerelease; not signed with a trusted developer certificate/notarized.
