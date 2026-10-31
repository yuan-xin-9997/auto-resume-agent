# Auto Resume Agent v0.5.4

- Default monitoring cadence is 30 seconds with independently persisted Codex/OpenCode settings (5–3600 seconds) and CLI `interval` control.
- Adopt running Codex sessions as well as structured quota interruptions. New Codex state enables recovery; existing saved pauses/exclusions remain respected.
- Continue every eligible interrupted session when all blocking quotas recover. Prioritize session recovery over helper creation.
- The optional Codex helper now requires an observed exhausted five-hour window and no pending quota recovery; unused quota never creates a helper.
- Wall-clock waits and transport renewal after long gaps handle sleep/wake. Known blocked quotas reduce upstream polls to up to five-minute intervals while local checks and reset deadlines continue.
- Settings page scrolls on small displays; five locales updated.

Validation: 131 automated tests on the local Windows environment. Sleep/wake and quota exhaustion are simulated; no physical suspend/resume or new live quota-boundary experiment is claimed. Native builds run in CI; artifacts remain unsigned.
