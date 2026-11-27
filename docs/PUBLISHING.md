# Publishing

Where Sages can be installed from and listed, what each place needs, and who has to do it.
Statuses are as of 2026-11-27 for version 0.1.0. Update this file when one changes.

## Release steps

1. Bump the version in all ten manifests and check them: `uv run python scripts/check_release_integrity.py --root . --check-version-sync`.
2. Add the release to `CHANGELOG.md`.
3. Run every gate in [TESTING.md](../TESTING.md), then `uv run python scripts/reverify_remote.py --root .` and paste its dated line into `sources/PROVENANCE.md`.
4. Tag `vX.Y.Z` and push the tag. The release workflow builds the per-skill ZIPs and the wheel, attaches them to a GitHub release, and regenerates the `hermes` branch.

## Install paths

"Run here" means the path was exercised on the maintainer's machine. "Per vendor docs" means the
command follows that vendor's current documentation or the working reference repository
(agent-data/job-search) and has not been run here.

| Product | How it installs | Status |
|---|---|---|
| Hermes Agent | `hermes` branch cloned into `plugins/`, then `hermes plugins enable sages` | Run here on v0.23.4 from GitHub: enabled, `plugins doctor` passes |
| Any MCP client | `uvx --from git+https://github.com/NTP-996/sages sages-mcp` | Run here from GitHub: a stdio client listed six tools and told a real quotation from a fake one |
| opencode | `.opencode/plugins/sages.js` via the `plugin` array | Shim run under node in the test suite; not run inside opencode |
| Claude Code | `/plugin marketplace add NTP-996/sages` | Per vendor docs |
| Claude apps | upload a skill ZIP under Customize > Skills | Per vendor docs (support.claude.com) |
| ChatGPT | upload a skill ZIP under Skills > Create | Per vendor docs (help.openai.com) |
| ChatGPT workspace | Admin Console > Plugins > Add > Import marketplace | Per vendor docs; reads `.claude-plugin/marketplace.json` |
| Codex | `codex plugin marketplace add NTP-996/sages` | Per vendor docs |
| Cursor | symlink into `~/.cursor/plugins/local/` | Per reference repository |
| Gemini CLI | `gemini extensions install <repo url>` | Per vendor docs; skills are discovered in `skills/` |
| GitHub Copilot CLI | `copilot plugin marketplace add NTP-996/sages` | Per reference repository |
| Factory Droid | `droid plugin marketplace add <repo url>` | Per reference repository |
| Pi | `pi install git:github.com/NTP-996/sages` | Per reference repository |
| VS Code, Kiro, other Agent Plugins clients | root `plugin.json` (agent-plugins.org 1.0.0) | Manifest validated against the published schema's field list |

## Listings

Steps marked **owner** need the repository owner's account, a login, or a form.

| Where | What it needs | Who | Status |
|---|---|---|---|
| GitHub repository | public repo, topics `agent-skills`, `claude-code-plugin`, `gemini-cli-extension`, `mcp`, `hermes-agent` | **owner** (topics) | public since 2026-11-27; topics not set |
| GitHub release with ZIPs | tag push; Actions enabled | automatic | v0.1.0 released 2026-11-27 with nine skill ZIPs, the wheel and the sdist; the workflow also regenerated the `hermes` branch |
| Gemini CLI extensions gallery | the `gemini-cli-extension` topic on the public repo | **owner** | not done |
| Claude plugin directories | a public repo with `.claude-plugin/marketplace.json`; Anthropic's own directory takes submissions by form | **owner** | not submitted |
| ChatGPT / Codex plugin directory | OpenAI's publishing flow for public plugins | **owner** | not submitted |
| Cursor marketplace | Cursor's submission flow | **owner** | not submitted |
| Hermes plugin catalog | a pull request adding `plugin-catalog/sages.yaml` to NousResearch/hermes-agent, pinned to a commit of the `hermes` branch, with a disclosure line | **owner** | not submitted |
| skills.sh | none: `npx skills add NTP-996/sages` works on any public repo with a `skills/` folder | automatic | untested |
| Pi packages | `pi-package` keyword in `package.json` (present); listing needs an npm publish | **owner** | not published |
| PyPI (`sages-mcp`) | `uv build && uv publish` with a PyPI token | **owner** | not published; the git install works without it |
| MCP Registry | PyPI package first, then `mcp-publisher login github && mcp-publisher publish` with `server.json` | **owner** | waiting on PyPI |
| Other MCP directories (Smithery, Glama, PulseMCP, mcp.so) | each indexes public repos or takes a form | **owner** | not submitted |

## A hosted MCP endpoint

ChatGPT connects to custom MCP servers only over HTTPS, not to a local process. `sages-mcp
--transport streamable-http` runs the server on a port, but nobody hosts a public endpoint, so
ChatGPT users install skills instead. Hosting one is a later decision: it has a running cost.
