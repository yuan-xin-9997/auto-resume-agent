# Upgrade and rollback

The application and its local state are separate. Upgrading replaces program
files; it does not require deleting the state directory. Keeping state is what
prevents an already-claimed interruption from being submitted again.

## Before upgrading

1. Stop the GUI and any `auto-resume-agent watch`/`check` process.
2. Note the current version (`auto-resume-agent --version`, or the GUI sidebar).
3. Back up the state directory while the app is stopped. On Windows, for
   example:

   ```powershell
   Copy-Item -Recurse "$env:LOCALAPPDATA\AutoResumeAgent" "$env:LOCALAPPDATA\AutoResumeAgent.backup"
   ```

   On Linux/macOS, copy `${XDG_STATE_HOME:-~/.local/state}/auto-resume-agent` or
   `~/Library/Application Support/AutoResumeAgent` with your normal backup tool.
4. Verify the new archive's adjacent `.sha256` file before extracting or
   installing.

## Upgrade

- **Windows:** run the new `Install.cmd`; it updates the stable per-user install
  and keeps `%LOCALAPPDATA%\AutoResumeAgent` state. `Launch.cmd` remains portable.
- **Linux:** extract the new tarball and run `sh install.sh`.
- **macOS:** extract the new tarball and run `sh install.sh`, then open the app
  from `~/Applications`.
- **From source:** install the new checkout into the same virtual environment,
  or replace the package and run the tests before restarting the monitor.

After starting, confirm the displayed version, existing watched sessions, and
saved settings. Recovery should still be paused if it was paused before the
upgrade. Run `doctor` after an agent update; a compatibility failure blocks
automatic sending.

## Rollback

1. Stop the application.
2. Reinstall the previous archive over the program files.
3. If the older version cannot read the state created by the newer version,
   restore the backup taken before the upgrade. Do not delete state merely to
   make the app start: that can discard cancellation and delivery-claim history.
4. Start the older version and verify the version, watched sessions, and
   recovery records. Do not re-enable recovery until the state is understood.

The SQLite schema is created idempotently for the current release, but this
project does not promise that every future schema will be readable by every
older release. A backup is the reliable rollback path.

## Signing status

Release archives produced from this repository are **unsigned and not
notarized** by default. Upgrading does not change OS security settings. Optional
maintainer signing steps are documented in [SIGNING.md](SIGNING.md); they are not
part of the default build. Code signing and Apple notarization remain external
release tasks when no certificate is available.

## State details

See [STATE_DIRECTORY.md](STATE_DIRECTORY.md) for paths, files, permissions, and
backup guidance.
