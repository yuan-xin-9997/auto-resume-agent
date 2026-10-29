# Protocol regression fixtures

These files are **synthetic, sanitized shape samples**, not captures from a real
account. They document the response fields the adapters rely on for the
versions listed in `docs/COMPATIBILITY.md`:

- Codex CLI `0.163.0` app-server (experimental)
- OpenCode server `1.19.3`

They contain only synthetic IDs, numeric quota values and classified error
fields. No prompts, transcripts, account details, access tokens or provider
credentials are stored here. When a real sample is added later, remove all
conversation text, paths, account identifiers and credentials first, and say so
in this file. Tests must never read a developer's real Codex/OpenCode state.
