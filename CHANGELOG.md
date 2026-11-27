# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-27

### Added

- Seven teacher portrayals as self-contained Agent Skills: Laozi, the Buddha, Confucius,
  Epictetus, Marcus Aurelius, Carl Jung and Charlie Munger.
- `sage-council`, which puts one question to several teachers and reports where they agree and
  where they differ, and `sages`, the front door.
- 243 passages: 204 from public-domain and CC0 translations committed under `sources/` and 18
  from Jung's 1916-17 English editions (excerpts only), all checked word for word against those
  files on every change; and 21 short cited lines from Munger's public talks, checked against
  the live transcripts before release.
- Manifests for Claude Code, Codex, Cursor, Factory Droid, Gemini CLI, Pi, opencode and Hermes
  Agent, and a root `plugin.json` in the Agent Plugins format for ChatGPT, VS Code, Kiro and
  other clients.
- `sages-mcp`, an MCP server over the same files: six tools including `verify_quote`, a prompt
  per teacher and one for the council. It makes no model calls.
- A ZIP per skill for chat apps that take uploaded skills, and a `hermes` branch for Hermes Agent.
