"""The result of checking a claimed quotation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sages_mcp.models.passage import Passage

QuoteStatus = Literal["verified", "in-source", "close", "not-found"]


@dataclass(frozen=True, slots=True)
class QuoteCheck:
    """How a claimed quotation stands against the verified passages and bundled sources.

    verified  - the words are part of a verified passage.
    in-source - the words are in a bundled source text, under source_citation.
    close     - not word for word; matches holds the recorded wording.
    not-found - in neither; the note says what that does and does not mean.
    """

    status: QuoteStatus
    matches: tuple[Passage, ...]
    source_citation: str | None
    note: str
