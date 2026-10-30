# State directory

Auto Resume Agent keeps its own local state separately from the agent's data.
The directory can be overridden with `--home PATH` or the `ARA_HOME`
environment variable.

| OS | Default state directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%\AutoResumeAgent` |
| Linux | `${XDG_STATE_HOME:-~/.local/state}/auto-resume-agent` |
| macOS | `~/Library/Application Support/AutoResumeAgent` |

`CODEX_HOME` selects the Codex profile, not this application's state. Watched
sessions are bound to the selected Codex home.

## Contents

| Path | Purpose |
| --- | --- |
| `state.sqlite3` | Settings, watched session IDs, classified recovery records, numeric quota snapshots, bounded event codes, and optional window-start claims. |
| `monitor.lock` | Cross-process lock; only one sender per state directory should run. The OS releases it after a crash. |
| `opencode/<hash>/state.sqlite3` | Separate state for each OpenCode URL + workspace identity. |

The database does **not** store prompts, full transcripts, raw provider errors,
access tokens, API keys, or OpenCode server passwords. Session titles and
workspace paths are displayed in memory and can be printed by the `sessions`
CLI command; treat redirected output as private.

`ARA_DEBUG_LOG` is an optional, off-by-default troubleshooting file containing
Codex app-server stderr. It may contain private paths or error details and is
separate from the state database. Review it before sharing.

## Permissions and backup

The state directory is created with user-only permissions where the platform
supports them, and the SQLite file is set to mode `0600` on non-Windows systems.
Back up the directory only while the application is stopped, or use a SQLite
online-backup tool. Restoring an old state can reintroduce an already-claimed
delivery, so restore deliberately and keep the backup until the session state is
verified.

Removing the state directory discards settings, watched sessions, cancellations,
and delivery claims. It does not delete Codex/OpenCode data. See
[UPGRADING.md](UPGRADING.md) for upgrade and rollback steps.

Session names are also cached in the local `session_names` table for activity labels after restart. Names can contain personal information; the cache is part of state backups. Workspace paths are not added to this cache.
