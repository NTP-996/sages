# Testing

Everything below runs offline except where noted. Run all of it before opening a pull request.

```bash
uv sync
uv run pytest --cov=src/sages_mcp           # unit and in-process MCP tests, coverage gate 80%
uv run ruff check . && uv run ruff format --check .
uv run mypy                                 # strict, over src/ and scripts/
uv run python scripts/verify_passages.py --root .     # every passage is in its source
uv run python scripts/quote_guard.py --root .         # no unverified quotation in a skill
uv run python scripts/eval_lint.py --root .           # scenario suites are well formed
uv run python scripts/check_release_integrity.py --root . --check-version-sync
uv run pip-audit                            # known vulnerabilities in dependencies
uv build                                    # the wheel bundles skills/ and sources/
```

CI runs the same commands (`.github/workflows/ci.yml`).

## What the tests cover

| Area | Tests |
|---|---|
| Passages match their sources | `test_verify_passages.py`, and the real tree through the script |
| No unverified quotation in a skill | `test_quote_guard.py` |
| Source files and provenance | `test_sources.py`, `test_sources_common.py` |
| Skills: frontmatter, sections, shared ground rules, budgets | `test_skills.py`, `test_roster.py` |
| Scenario suites | `test_eval_lint.py` |
| Manifests, version sync | `test_manifests.py`, `test_release_integrity.py` |
| Hermes adapter, opencode shim | `test_hermes_plugin.py`, `test_opencode_plugin.py` (needs node) |
| Release artefacts | `test_build_dist.py` |
| MCP server | `test_mcp_services.py` (fake repository), `test_mcp_server.py` (the SDK client in process), `test_mcp_repositories.py`, `test_mcp_main.py` (also builds the wheel) |
| Docs | `test_docs.py` |

## Needs the network

```bash
uv run python scripts/reverify_remote.py --root .
```

Fetches each Munger passage's source page and rebuilds the full Jung editions, then re-checks the
passages. Run it before a release and record its dated line in `sources/PROVENANCE.md`.

## Behaviour

Structure is tested; whether a portrayal behaves is graded by running the scenarios in
`skills/<skill>/evals/evals.json` against a model: load the skill, send the prompt, and check the
reply against each expectation. Any quoted span of eight or more words in a reply must be a
passage. This needs a model, so it is not part of CI.
