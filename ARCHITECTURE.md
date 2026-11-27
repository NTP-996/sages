# Architecture

Sages is one tree of markdown and data, read in place by every harness, with dev tooling around
it that keeps the quotations honest. This file is the map; the details live where it points.

## The parts

```
skills/                 the content, and the only copy of it
  <teacher>/SKILL.md      a portrayal: who is speaking, how he talks, what he teaches,
                          how he meets a question, passages, ground rules, limits
  <teacher>/passages.jsonl  his verified quotations
  sages/                  the front door and roster.json (who sits, in what order)
  sage-council/           one question, several voices
  */evals/evals.json      scenario suites
sources/                the texts the passages are checked against, and PROVENANCE.md
src/sages_mcp/          the MCP server, reading skills/ and sources/ as package data
scripts/                dev tooling; nothing here ships to a harness
<manifests>             one per harness, all pointing at skills/
```

## How a quotation gets in

1. `scripts/sources/build_<teacher>.py` downloads one edition, strips what is not the
   translator's text, inserts a `## <citation>` heading per chapter, section, discourse or verse,
   and fails unless every paragraph it wrote is in the download word for word.
2. A passage is added to `skills/<teacher>/passages.jsonl` with the heading it sits under.
3. `scripts/verify_passages.py` fails unless the passage is a contiguous span of that source
   under that heading.
4. `scripts/quote_guard.py` fails if a skill quotes anything that is not such a passage.

Jung and Munger differ because their work is in copyright: see
[docs/decisions/0003-modern-figures.md](docs/decisions/0003-modern-figures.md).

## The portrayal contract

The seven portrayals carry one identical block of ground rules: say plainly that this is a
portrayal when sincerely asked, quote only verified passages, step out of the voice for danger or
professional matters, drop the voice for ordinary work. A test fails if the seven copies differ.
Each skill is self-contained so that a registry can install one teacher's folder alone.

## Distribution

Every harness reads its own manifest and all of them point at `skills/`:
`plugin.json` (Agent Plugins), `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`,
`.factory-plugin/`, `gemini-extension.json`, `package.json` (Pi and opencode), and
`plugin.yaml` with `__init__.py` (Hermes Agent). No manifest starts the MCP server.
`scripts/check_release_integrity.py` keeps their versions in step.

Two artefacts are built instead of cloned (`scripts/build_dist.py`): a ZIP per skill for chat apps
that take uploaded skills, and the `hermes` branch, which holds only what Hermes Agent needs
because its installer scans the whole tree.

## The MCP server

```
controllers/   tools, prompts, resources: parse, call one service, shape the reply
services/      SageService (roster, portrayals, council), PassageService (search, verify_quote)
repositories/  Protocols, and filesystem implementations over skills/ and sources/
models/        Sage, Persona, CouncilBrief, Passage, QuoteCheck
```

Services depend on the repository Protocols, never on the filesystem classes. The server makes
no model call: it hands the calling model a portrayal and verified passages, and the model
writes the reply. Decisions are recorded in [docs/decisions/](docs/decisions/).
