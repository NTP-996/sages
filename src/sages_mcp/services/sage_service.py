"""Who the teachers are, how to speak as one, and how to convene several."""

from __future__ import annotations

from collections.abc import Sequence

from sages_mcp.models import CouncilBrief, Persona, Sage
from sages_mcp.repositories import SageRepository
from sages_mcp.utils.text import loose

COUNCIL_SKILL = "sage-council"


class UnknownSageError(ValueError):
    """Raised when a name matches no teacher. The message lists the valid ids."""

    def __init__(self, given: str, valid: Sequence[str]) -> None:
        super().__init__(f"No teacher is called {given!r}. Choose one of: {', '.join(valid)}.")
        self.given = given
        self.valid = tuple(valid)


class SageService:
    """The roster and the portrayals built on it."""

    def __init__(self, repository: SageRepository) -> None:
        self._repository = repository
        self._by_name: dict[str, Sage] = {}
        for sage in repository.roster():
            for name in (sage.id, sage.name, *sage.aliases):
                self._by_name.setdefault(loose(name), sage)

    def list(self) -> tuple[Sage, ...]:
        """Every teacher, in council order."""
        return self._repository.roster()

    def resolve(self, name: str) -> Sage:
        """Find a teacher by id, name or alias, ignoring case, spacing and punctuation."""
        sage = self._by_name.get(loose(name))
        if sage is None:
            raise UnknownSageError(name.strip(), [s.id for s in self._repository.roster()])
        return sage

    def persona(self, name: str) -> Persona:
        """The instructions for speaking as one teacher."""
        sage = self.resolve(name)
        return Persona(
            sage=sage,
            instructions=self._repository.skill_body(sage.id),
            passage_count=len(self._repository.passages(sage.id)),
        )

    def council(self, question: str, names: Sequence[str] | None) -> CouncilBrief:
        """The council protocol and each chosen teacher's instructions, in council order."""
        if not question.strip():
            raise ValueError("The council needs a question.")
        chosen = {self.resolve(name).id for name in names} if names else None
        voices = tuple(
            self.persona(sage.id)
            for sage in self._repository.roster()
            if chosen is None or sage.id in chosen
        )
        return CouncilBrief(
            question=question.strip(),
            protocol=self._repository.skill_body(COUNCIL_SKILL),
            voices=voices,
        )
