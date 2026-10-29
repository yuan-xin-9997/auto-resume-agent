# Auto Resume Agent v0.5.2

Stability and compatibility preparation. This source change does not create a
tag or publish a release.

- `doctor` now reports `compatible`, the failing read-only check, and
  `automatic_sending: blocked` when an experimental method or response field is
  missing. It never submits a continuation.
- Codex and OpenCode adapters reject changed response shapes explicitly instead
  of guessing; an interface incompatibility stops all automatic sending for that
  monitor pass.
- Quota snapshots with an unreadable window no longer use another window's reset
  time to authorize delivery. Unknown quota keeps waiting.
- A pause, unwatch, or explicit cancel after a durable claim but before the
  process boundary is honored. Ambiguous delivery remains `uncertain` and is
  never blindly resent.
- Added synthetic, sanitized protocol fixtures for the documented Codex
  `0.163.0` and OpenCode `1.19.3` baselines, plus version/package/evidence
  consistency checks.
- Added contribution, security, upgrade/rollback, state-directory, signing and
  release-checklist documentation. Artifacts remain unsigned and not notarized;
  signing/notarization are optional external release tasks.
- Windows builds now add Conda's `Library/bin` to the PyInstaller DLL search
  path, so bundled executables include native libraries such as SQLite.

# Auto Resume Agent v0.5.1

Refresh the interface with a clean neutral light palette, white surfaces, restrained charcoal controls, gray progress bars and consistent borders. Remove the competing green/blue status colors, reduce oversized headings and simplify scrollbars. Monitoring, recovery and persisted configuration behavior are unchanged.

Includes native GUI/CLI bundles and SHA-256 files for Windows x64, Linux x64 and macOS arm64/x64. Prerelease; unsigned and not notarized.
