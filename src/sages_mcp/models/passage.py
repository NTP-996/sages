"""A verified quotation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Passage:
    """One quotation, exactly as its source prints it, with where it comes from."""

    id: str
    sage: str
    text: str
    citation: str
    work: str
    themes: tuple[str, ...]
    translator: str | None = None
    year: int | None = None
    note: str | None = None
    source_url: str | None = None
