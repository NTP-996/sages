"""Finding verified passages and checking claimed quotations against them."""

from __future__ import annotations

from collections import Counter

from sages_mcp.models import Passage, QuoteCheck
from sages_mcp.repositories import SageRepository, SourceRepository
from sages_mcp.services.sage_service import SageService
from sages_mcp.utils.text import loose, words

DEFAULT_LIMIT = 5
MAX_LIMIT = 20
MIN_QUOTE_WORDS = 6
CLOSE_THRESHOLD = 0.6

NOT_FOUND_NOTE = (
    "Not found in the verified passages or in the bundled source texts. Other translations "
    "word things differently, and for Jung and Munger only a few passages are bundled, so this "
    "is not proof that the line is spurious. Do not put it in quotation marks: give the idea in "
    "your own words, and say that you could not find it in the recorded words."
)


class PassageService:
    """Search and verification over the passages of every teacher."""

    def __init__(
        self, repository: SageRepository, sources: SourceRepository, sages: SageService
    ) -> None:
        self._repository = repository
        self._sources = sources
        self._sages = sages

    def _pool(self, sage: str | None) -> list[Passage]:
        teachers = [self._sages.resolve(sage)] if sage else list(self._sages.list())
        return [
            passage for teacher in teachers for passage in self._repository.passages(teacher.id)
        ]

    def find(
        self,
        sage: str | None = None,
        theme: str | None = None,
        query: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> tuple[Passage, ...]:
        """Passages of one teacher or of all, filtered by theme and by query words."""
        wanted_theme = theme.strip().lower() if theme and theme.strip() else None
        wanted_words = words(query) if query else []
        found: list[Passage] = []
        for passage in self._pool(sage):
            if wanted_theme and wanted_theme not in passage.themes:
                continue
            haystack = set(
                words(" ".join((passage.text, passage.citation, passage.work, *passage.themes)))
            )
            if all(word in haystack for word in wanted_words):
                found.append(passage)
        return tuple(found[: max(1, min(limit, MAX_LIMIT))])

    def all_for(self, sage: str) -> tuple[Passage, ...]:
        """Every verified passage of one teacher, in file order."""
        return tuple(self._pool(sage))

    def themes(self) -> dict[str, int]:
        """Every theme with the number of passages tagged with it, most used first."""
        counts = Counter(theme for passage in self._pool(None) for theme in passage.themes)
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    def verify_quote(self, text: str, sage: str | None = None) -> QuoteCheck:
        """Say whether text is a teacher's recorded words. Complexity: O(passages + source text)."""
        teacher = self._sages.resolve(sage) if sage else None
        claimed = loose(text)
        claimed_words = set(claimed.split())
        pool = self._pool(sage)
        whole = tuple(passage for passage in pool if claimed and claimed == loose(passage.text))
        if whole:
            return QuoteCheck("verified", whole, None, "This is a verified passage, word for word.")
        if len(claimed.split()) < MIN_QUOTE_WORDS:
            return QuoteCheck(
                "not-found",
                (),
                None,
                "Too short to check reliably: give at least six words of the line.",
            )
        # Compare whole words: "reliable" must not match inside "unreliable".
        exact = tuple(passage for passage in pool if f" {claimed} " in f" {loose(passage.text)} ")
        if exact:
            return QuoteCheck(
                "verified", exact, None, "These words are part of a verified passage."
            )
        hit = self._sources.search(claimed, teacher.id if teacher else None)
        if hit is not None:
            teacher_id, heading = hit
            return QuoteCheck(
                "in-source",
                (),
                heading,
                f"Found in the bundled source text for {teacher_id}, under {heading}. This tool "
                "has not checked who is speaking there: it may be a student, an opponent or "
                "someone he is quoting. Read the section before attributing the line to him.",
            )
        best, score = None, 0.0
        for passage in pool:
            passage_words = set(words(passage.text))
            overlap = len(claimed_words & passage_words) / len(claimed_words | passage_words)
            if overlap > score:
                best, score = passage, overlap
        if best is not None and score >= CLOSE_THRESHOLD:
            return QuoteCheck(
                "close",
                (best,),
                None,
                "Not word for word. The recorded wording is given: quote that instead.",
            )
        return QuoteCheck("not-found", (), None, NOT_FOUND_NOTE)
