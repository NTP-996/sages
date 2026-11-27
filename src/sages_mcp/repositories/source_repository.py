"""The bundled source texts, searchable by loosely normalised wording."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from sages_mcp.utils.text import loose


class SourceRepository(Protocol):
    """Full-text lookup over the source texts that ship with the package."""

    def search(self, loose_text: str, sage_id: str | None) -> tuple[str, str] | None:
        """Return (teacher id, heading) of the first section containing loose_text, or None."""


class FileSourceRepository:
    """Reads sources/<teacher>/*.txt, where "## <citation>" lines open each section.

    Loaded on first use: O(total text) once, then O(text) per search, which is fine for a few
    megabytes and avoids an index that would have to be kept in step with the files.
    """

    def __init__(self, data_dir: Path) -> None:
        self._sources = data_dir / "sources"
        self._sections: dict[str, list[tuple[str, str]]] | None = None

    def _load(self) -> dict[str, list[tuple[str, str]]]:
        sections: dict[str, list[tuple[str, str]]] = {}
        for path in sorted(self._sources.glob("*/*.txt")):
            heading: str | None = None
            lines: list[str] = []
            found = sections.setdefault(path.parent.name, [])
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("## "):
                    if heading is not None:
                        found.append((heading, f" {loose(chr(10).join(lines))} "))
                    heading, lines = line[3:].strip(), []
                else:
                    lines.append(line)
            if heading is not None:
                found.append((heading, f" {loose(chr(10).join(lines))} "))
        return sections

    def search(self, loose_text: str, sage_id: str | None) -> tuple[str, str] | None:
        if self._sections is None:
            self._sections = self._load()
        if not loose_text:
            return None
        needle = f" {loose_text} "  # whole words only: sections are stored padded the same way
        for teacher, sections in self._sections.items():
            if sage_id is not None and teacher != sage_id:
                continue
            for heading, text in sections:
                if needle in text:
                    return teacher, heading
        return None
