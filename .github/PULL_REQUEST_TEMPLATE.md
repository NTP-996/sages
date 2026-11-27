## What changes and why

## Checks

- [ ] `uv run pytest --cov=src/sages_mcp`
- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy`
- [ ] `uv run python scripts/verify_passages.py --root .`
- [ ] `uv run python scripts/quote_guard.py --root .`
- [ ] `uv run python scripts/check_release_integrity.py --root . --check-version-sync`
- [ ] Every new quotation was cut from a file under `sources/`, not typed
- [ ] Version bumped in all manifests if anything under `skills/` or `src/` changed
