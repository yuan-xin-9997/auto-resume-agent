# Local Windows updates

After publishing a release for this project, also deploy that version on the user's development Windows PC. A successful GitHub release alone is not completion: verify the version actually running locally. Preserve settings, watched sessions, recovery records and feature opt-ins. Never turn on the window starter merely to test an upgrade.

1. Download the published Windows archive and its SHA-256 file; verify before extracting.
2. Close any legacy Auto Resume Agent GUI running from old extracted workspace folders. Do not stop the separate Codex Auto Resume reference product.
3. Run the extracted `cli/auto-resume-agent.exe install` or `Install.cmd`.
4. The installer deploys to `%LOCALAPPDATA%/Programs/AutoResumeAgent`, creates Desktop/Start Menu shortcuts and retargets existing Auto Resume Agent shortcuts. It retains an adjacent previous-install backup when replacing a stable installation.
5. State remains in `%LOCALAPPDATA%/AutoResumeAgent` (or the user's configured state directory). The installer refuses an installation whose state directory is inside the files being replaced.
6. Start the stable `gui/AutoResumeAgent.exe` and verify its displayed version and the requested UI changes. Confirm the existing monitored sessions/settings remain intact.

Repeat this local step after subsequent releases in this task. This is a per-release deployment workflow, not a background update checker or an unattended download policy.
