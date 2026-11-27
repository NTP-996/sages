"""The roster, the skill texts and the verified passages."""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Protocol

from sages_mcp.models import Passage, Sage


class SageRepository(Protocol):
    """What the services need to know about the teachers."""

    def roster(self) -> tuple[Sage, ...]:
        """Every teacher, in council order."""

    def skill_body(self, skill: str) -> str:
        """The text of a skill without its frontmatter. Raises KeyError for an unknown skill."""

    def passages(self, sage_id: str) -> tuple[Passage, ...]:
        """The verified passages of one teacher, in file order."""


class FileSageRepository:
    """Reads the skills tree: skills/sages/roster.json, skills/<id>/SKILL.md and passages.jsonl."""

    def __init__(self, data_dir: Path) -> None:
        self._skills = data_dir / "skills"
        self._passages: dict[str, tuple[Passage, ...]] = {}

    @cached_property
    def _roster(self) -> tuple[Sage, ...]:
        entries = json.loads((self._skills / "sages" / "roster.json").read_text(encoding="utf-8"))
        return tuple(
            Sage(
                id=entry["id"],
                name=entry["name"],
                aliases=tuple(entry["aliases"]),
                era=entry["era"],
                tradition=entry["tradition"],
                one_line=entry["one_line"],
            )
            for entry in entries
        )

    def roster(self) -> tuple[Sage, ...]:
        return self._roster

    def skill_body(self, skill: str) -> str:
        path = self._skills / skill / "SKILL.md"
        if "/" in skill or "\\" in skill or not path.is_file():
            raise KeyError(skill)
        text = path.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            text = text[text.index("\n---\n", 4) + 5 :]
        return text.strip() + "\n"

    def passages(self, sage_id: str) -> tuple[Passage, ...]:
        if sage_id not in self._passages:
            path = self._skills / sage_id / "passages.jsonl"
            lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
            self._passages[sage_id] = tuple(
                _passage(json.loads(line)) for line in lines if line.strip()
            )
        return self._passages[sage_id]


def _passage(record: dict[str, object]) -> Passage:
    themes = record.get("themes")
    year = record.get("year")
    return Passage(
        id=str(record["id"]),
        sage=str(record["sage"]),
        text=str(record["text"]),
        citation=str(record["citation"]),
        work=str(record["work"]),
        themes=tuple(str(theme) for theme in themes) if isinstance(themes, list) else (),
        translator=_optional(record.get("translator")),
        year=year if isinstance(year, int) else None,
        note=_optional(record.get("note")),
        source_url=_optional(record.get("source_url")),
    )


def _optional(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
