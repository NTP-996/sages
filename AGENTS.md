# Sages - agent map

Seven teacher portrayals as Agent Skills, a council skill, an MCP server over the same files, and
tooling that checks every quotation against its source. This file is the entry point for coding
agents working on the repository.

## Start here

- [ARCHITECTURE.md](ARCHITECTURE.md): the parts and how a quotation gets in.
- [CONTRIBUTING.md](CONTRIBUTING.md): the rules a change must not break, and how to add a teacher.
- [TESTING.md](TESTING.md): every gate and how to run it.

## Rules that are enforced

- A quotation in any `SKILL.md` must be a record in that skill's `passages.jsonl`
  (`scripts/quote_guard.py`), and every record must be word for word in its source
  (`scripts/verify_passages.py`). Never type a quotation from memory: cut it from the source.
- The ground-rules block is byte-identical in the seven portrayals. Change it in all seven.
- A portrayal names no file except `passages.jsonl`, and no `SKILL.md` contains `../`.
- Only markdown and data live under `skills/`. Dev tooling is in `scripts/` and never ships.
- All ten manifests carry one version (`scripts/check_release_integrity.py`).
- No personal data in the tree, and no commit authored with a personal mailbox.

## Working here

- `uv sync`, then `uv run pytest`. Scripts under `scripts/` use the standard library only.
- The MCP server keeps controllers thin, logic in services, file access in repositories.
- Conventional commits with a scope: `feat(skills): ...`, `fix(mcp): ...`, `docs: ...`.
