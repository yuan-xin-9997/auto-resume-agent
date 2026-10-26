# Auto Resume Agent v0.4.2

Fix the session status after watching a previously cancelled session again. An old cancelled recovery no longer hides the current active watch: the row immediately displays Watching (监控中) and stays correct after refresh.

Historical cancellation records remain intact; watching again does not reset delivery claims or replay cancelled requests. Applies to both Codex and OpenCode session lists.

75 automated tests include the watch → unwatch → cancelled → watch-again sequence, refreshed status, and unchanged cancellation history. Native GUI/CLI bundles and SHA-256 files are provided for Windows x64, Linux x64 and macOS arm64/x64.

Windows Install.cmd updates the stable per-user installation while preserving settings, watched sessions, recovery history and feature opt-ins. Prerelease; unsigned and not notarized. Existing provider and recovery limitations remain documented in docs/TESTING.md.
