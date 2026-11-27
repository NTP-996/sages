# CLAUDE.md

Coding agents working on this repository: read [AGENTS.md](AGENTS.md). It points to the
architecture, the enforced rules and the test gates.

Two things are easy to get wrong here:

- **Never write a quotation from memory.** Cut it from the file under `sources/` and let
  `scripts/verify_passages.py` confirm it. A remembered line that is one word off fails CI, and a
  remembered line that is plausible but wrong is exactly what this project exists to prevent.
- **Measure before stating a number.** Passage counts, word counts and coverage come from running
  the command, and the sentence should say which command.
