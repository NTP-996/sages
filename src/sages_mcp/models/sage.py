"""A teacher, his portrayal, and a council of several."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Sage:
    """One teacher on the roster."""

    id: str
    name: str
    aliases: tuple[str, ...]
    era: str
    tradition: str
    one_line: str


@dataclass(frozen=True, slots=True)
class Persona:
    """A teacher with the instructions a model follows to speak as him."""

    sage: Sage
    instructions: str
    passage_count: int


@dataclass(frozen=True, slots=True)
class CouncilBrief:
    """Everything a model needs to answer one question in several voices."""

    question: str
    protocol: str
    voices: tuple[Persona, ...]
