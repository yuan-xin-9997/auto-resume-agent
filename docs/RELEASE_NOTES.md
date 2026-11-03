# Unreleased — OpenCode 2.x adapter

- Auto-detect OpenCode 2.x `/api` services behind the existing 1.19.x health probe; Basic auth uses `OPENCODE_SERVER_PASSWORD`.
- Read OpenCode Go/Go Plus rolling, weekly and monthly allowance and reset times from `/api/experimental/usage/limits`; schedule Go quota recovery at the reported reset.
- Map 2.x `provider.*` errors, block active/permission/form/retry states, and submit through `/api/session/{id}/prompt` with `delivery: queue` and `resume: true`.
- Add specific `opencode_connection_failed` and `opencode_auth_required` messages; 2.x prompts use the session's current model, agent and variant.
- Show **Connecting…** during the initial connection check and **Pending** for usage cards without data instead of a bare Unknown state.
- Give the Refresh button immediate **Refreshing…** feedback, a slow-check hint after 5 seconds, and a timeout hint after 20 seconds when the background monitor is busy or unresponsive.
- Re-evaluate watched sessions on every check for both Codex and OpenCode: running/active sessions and sessions with an active recovery stay watched; completed or interrupted sessions with no outstanding work are automatically unwatched after a short grace period without a permanent exclusion; quota-exhausted or queued recoveries remain until resolved.
- Mark a Codex recovery that stays queued for 10 minutes as **Needs attention** with a `Queued too long` detail instead of leaving it queued forever; queued and stale records can be cancelled or unwatched.
- Add a user-confirmed **Retry queued task** action. It resumes the exact stored thread and starts one turn with `approvalPolicy: never`; it warns that the original queued message may still exist and that permission approvals still require the original session. It never resends automatically, and an unconfirmed result becomes **Delivery uncertain**.
- Treat a Codex Desktop turn reported as interrupted with no completion time as running while its thread has been updated within 180 seconds, so actively running desktop tasks are adopted instead of being hidden by the filter.
- Default the dashboard session filter to Watching; switch to All to select unmonitored sessions.
- Automatically adopt new running Codex and OpenCode sessions, plus OpenCode usage-limit failures. OpenCode uses the global active-session set so a new turn is re-adopted even when the cached `updatedAt` is unchanged, including sessions in other workspaces; watched sessions outside the configured page are added to the list. Refresh forces a discovery pass. Manual Unwatch exclusions still block re-adoption; automatic completion unwatch does not.
- Sync the desktop session list every 30 seconds while preserving loaded rows; the Refresh button still forces an immediate full refresh.
- Save pending connection fields when switching between Codex and OpenCode, and preserve each agent's own enabled/paused state and watch list. Explicit Save still pauses the selected agent as a safety measure.
- Validation: 178 automated tests; synthetic real 2.2.5 delivery in a temporary session (deleted afterward); a real persisted Codex thread was resumed and retried across two app-server processes, the retry turn completed, and the temporary thread was deleted; a real Codex app-server turn reported interrupted with no completion time was auto-adopted while its thread stayed active; `doctor` against the local desktop service reports known Go quota. The 2.x API remains experimental.

# Auto Resume Agent v0.5.5

- Rebuilt the desktop interface around a graphite and teal visual system, with a grouped dashboard header, clearer primary actions and consistent spacing, typography, focus and hover states.
- Reworked usage cards with remaining quota, severity labels, reset countdowns and animated progress; added a live sidebar status block and icon navigation.
- Added session search and status filters, compact status pills, project context, empty/loading states, selection actions and a denser activity timeline.
- Reorganized settings into general, Codex, OpenCode and advanced groups with a fixed save bar. Connection fields apply on save; language, theme and polling intervals save immediately.
- Added light, dark and system-following themes, page and control animations, keyboard shortcuts, accessible names and focus indicators.
- Persisted window geometry and the last visited page, and split reusable UI pieces into a dedicated `ui` package with bundled SVG icons.
- Preserved existing settings, watched sessions, recovery claims and all five locales.

Validation: 131 automated tests pass locally. The Windows x64 bundle starts through its CLI and GUI smoke checks, and installation over v0.5.4 preserves the existing state database. Native artifacts remain unsigned.

# Auto Resume Agent v0.5.4

- Default monitoring cadence is 30 seconds with independently persisted Codex/OpenCode settings (5–3600 seconds) and CLI `interval` control.
- Adopt running Codex sessions as well as structured quota interruptions. New Codex state enables recovery; existing saved pauses/exclusions remain respected.
- Continue every eligible interrupted session when all blocking quotas recover. Prioritize session recovery over helper creation.
- The optional Codex helper now requires an observed exhausted five-hour window and no pending quota recovery; unused quota never creates a helper.
- Wall-clock waits and transport renewal after long gaps handle sleep/wake. Known blocked quotas reduce upstream polls to up to five-minute intervals while local checks and reset deadlines continue.
- Settings page scrolls on small displays; five locales updated.

Validation: 131 automated tests on the local Windows environment. Sleep/wake and quota exhaustion are simulated; no physical suspend/resume or new live quota-boundary experiment is claimed. Native builds run in CI; artifacts remain unsigned.
