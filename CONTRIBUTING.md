# Contributing

Thanks for helping. A few rules keep the quotations honest and the pack portable; the test suite
enforces most of them.

## The rules

1. **A quotation is cut from a source, never typed.** Every passage in `skills/*/passages.jsonl`
   must be a word-for-word span of a file under `sources/`, under the heading it names. (Munger
   is the one exception: his passages cite a public transcript and are re-checked by
   `scripts/reverify_remote.py`.) The script proves the words are in the text; you must check
   who is speaking them. A student's saying in the Analects is not Confucius.
2. **Nothing is quoted in a skill unless it is a passage.** Paraphrase with a citation instead.
3. **Sources must be free to redistribute.** Public domain everywhere, or CC0. A figure whose
   work is still in copyright needs the treatment described in
   [docs/decisions/0003-modern-figures.md](docs/decisions/0003-modern-figures.md), and an issue
   first.
4. **The seven portrayals share one ground-rules block.** Edit it in all seven or not at all.
5. **A portrayal stands alone.** It may name no file but `passages.jsonl`.
6. **Keep the voices apart.** If a change makes two teachers sound alike, it is the wrong change.
7. **Bump the version in every manifest** when anything under `skills/` or `src/` changes.

## Adding a teacher

1. Open an issue naming the teacher, the translation and why it is free to redistribute.
2. Write `scripts/sources/build_<id>.py` (copy the nearest existing one). It must download the
   edition, insert one `## <citation>` heading per citable unit, and pass the no-words-changed
   check. Run it; it writes `sources/<id>/` and the entry in `sources/PROVENANCE.md`.
3. Add `skills/<id>/passages.jsonl`: 25 to 45 passages, each cut from the source, tagged from the
   theme list in use (the `list_themes` tool of the MCP server prints it). Add the id to `SOURCE_POLICY` in `scripts/verify_passages.py`.
4. Write `skills/<id>/SKILL.md` with the seven sections in order and the shared ground-rules
   block copied exactly. Keep the body under 1,600 words.
5. Add the teacher to `skills/sages/roster.json`, to the front door and the council skill, to
   `SKILLS` in `__init__.py`, and to the lists in `tests/`.
6. Add `skills/<id>/evals/evals.json` with at least the six required scenario kinds.
7. Run every gate in [TESTING.md](TESTING.md).

## Commit messages

Conventional commits with a scope: `feat(skills): add Seneca`, `fix(mcp): clamp limit`,
`docs: clarify the Hermes install`. Imperative mood, under about 72 characters.

## Versioning

Semantic versioning. Patch for fixes and wording, minor for a new teacher or tool, major for a
change that breaks an installed pack. Ten files carry the version; the release-integrity check
names any that disagree.
