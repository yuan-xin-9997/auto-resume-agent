# Auto Resume Agent v0.1.0

First cross-platform prerelease: Codex quota monitoring and exact-session recovery, native Qt GUI, CLI, English/简体中文/繁體中文/日本語/한국어, durable recovery state, bounded retries and platform icons.

Native archives include GUI and CLI for Windows x64, Linux x64, macOS Apple Silicon and Intel, with SHA-256 files. Codex CLI is an external requirement; tested integration baseline is 0.163.0.

Read the README and docs/TESTING.md before enabling. This release supports Codex, not all AI agents. `Queued` is not execution confirmation; keep the original session open. Ambiguous delivery is never blindly retried. Targets include Windows 10/11, Ubuntu 24/26 and macOS 27; the testing matrix distinguishes actual hardware checks from CI and forward compatibility. Binaries are unsigned/not notarized.
