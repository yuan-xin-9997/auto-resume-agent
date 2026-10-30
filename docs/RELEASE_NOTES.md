# Auto Resume Agent v0.5.3

- Skip creating a Codex window helper when the server already reports an active new five-hour window; follow its reset deadline instead.
- Search loaded Codex/OpenCode sessions by name, UUID or workspace. Bulk actions affect visible checked sessions only.
- Show session names alongside UUIDs in activity history, with a durable local name cache.
- Preserve existing settings, monitored sessions and recovery records on upgrade.

Validation: 124 automated tests on the local Windows environment; native platform builds run in CI. Other OS versions require device validation. Artifacts remain unsigned.
