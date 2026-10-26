# Auto Resume Agent v0.4.0

- Localized quota labels: 300 minutes becomes 5 hours; 10080 minutes becomes 1 week.
- Session checkboxes and Select all support batch watch/unwatch. Checked UUIDs survive refreshes; selection alone never changes monitoring.
- Aligned session headers and cells, clearer checkbox indicators and more room for session rows.
- Windows Install.cmd deploys to a stable per-user directory, updates Desktop/Start Menu shortcuts, and preserves existing settings, monitored sessions and recovery records.
- Updated English/Chinese documentation and illustrative screenshots.

74 automated tests pass, including translated labels, checkbox batch operations and package validation. Native CI builds Windows x64, Linux x64 and macOS arm64/x64 GUI + CLI bundles with SHA-256 files.

The optional Codex five-hour window starter remains disabled by default. Existing recovery and provider limitations still apply; see docs/TESTING.md. Prerelease; unsigned and not notarized.
