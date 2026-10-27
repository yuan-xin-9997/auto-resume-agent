# Auto Resume Agent v0.4.4

Fix watched sessions remaining idle after quota returns: explicitly watching a session now includes its latest eligible failure even when monitoring started more than one minute after the interruption. The previous one-minute cutoff silently skipped these failures.

Do not label an interrupted queue-placeholder turn as session progression. Queued delivery still requires the original Codex session to be loaded; queue acceptance alone is not confirmed execution. Cancelled/claimed recoveries remain protected against replay, and only explicitly watched sessions are considered.

85 tests pass, including old latest failures, cancelled recovery preservation and queue-placeholder handling. The preceding v0.4.3 five-hour helper was also observed at a real server boundary: automatically started about 12 seconds after expiry, sent 回复 OK, received OK, and the reported reset advanced five hours.

Windows installation preserves existing configuration and records. Native GUI/CLI bundles with SHA-256 files are included for Windows x64, Linux x64 and macOS arm64/x64. Prerelease; unsigned and not notarized.
