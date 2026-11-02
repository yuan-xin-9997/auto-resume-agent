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
