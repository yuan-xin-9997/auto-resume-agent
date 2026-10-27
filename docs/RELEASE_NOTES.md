# Auto Resume Agent v0.5.0

Automatically watch unfinished Codex sessions whose latest turn failed from quota exhaustion, enabled by default. GUI and CLI use paginated, bounded discovery with recent-session refreshes. Completed/cancelled turns, archives, subagents and five-hour helper sessions are excluded.

- Settings toggle and CLI auto-watch on/off/status; discovery does not enable recovery or change five-hour helper opt-ins.
- Manual unwatch exclusions persist across restarts; manual Watch removes an exclusion. Legacy cancelled/unwatched sessions remain excluded on upgrade.
- Existing quota checks, exact UUID delivery, durable no-replay claims and retry budgets remain active. A discovery listing failure does not block existing watched-session recovery.
- Five-language controls and guidance. OpenCode remains manually selected because it has no equivalent structured Codex quota-exhaustion signal.

99 tests cover discovery defaults and filters, paging/batching, changed-session priority, pause behavior, opt-outs, legacy migration, CLI controls and GUI localization. Includes native GUI/CLI bundles and SHA-256 checksums for Windows x64, Linux x64 and macOS arm64/x64. Prerelease; unsigned and not notarized.
