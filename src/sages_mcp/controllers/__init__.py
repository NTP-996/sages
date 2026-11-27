"""The MCP surface: tools, prompts and resources. Thin: parse, call one service, shape the reply."""

from __future__ import annotations

from sages_mcp.models import Passage, Sage


def sage_dict(sage: Sage) -> dict[str, object]:
    return {
        "id": sage.id,
        "name": sage.name,
        "era": sage.era,
        "tradition": sage.tradition,
        "one_line": sage.one_line,
        "aliases": list(sage.aliases),
    }


def passage_dict(passage: Passage) -> dict[str, object]:
    return {
        "id": passage.id,
        "sage": passage.sage,
        "text": passage.text,
        "citation": passage.citation,
        "work": passage.work,
        "translator": passage.translator,
        "year": passage.year,
        "themes": list(passage.themes),
        "note": passage.note,
        "source_url": passage.source_url,
    }
