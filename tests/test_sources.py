"""The committed source texts: structure, provenance, and nothing but the translator's words."""

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
PROVENANCE = SOURCES / "PROVENANCE.md"
SUTTA_CITATION = re.compile(r"^(DN|MN|SN|AN|Dhp|Ud|Iti|Snp) \d+(\.\d+)?$")


def source_files() -> list[Path]:
    return sorted(p for p in SOURCES.rglob("*.txt") if p.is_file())


def headings(relative: str) -> list[str]:
    text = (SOURCES / relative).read_text(encoding="utf-8")
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def provenance_sections() -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    for line in PROVENANCE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def provenance_field(relative: str, field: str) -> str:
    match = re.search(
        rf"^- {re.escape(field)}: (.+)$", provenance_sections()[relative], re.MULTILINE
    )
    assert match, f"{relative}: PROVENANCE.md has no '{field}' line"
    return match.group(1).strip()


def test_laozi_has_81_chapters() -> None:
    assert headings("laozi/legge-tao-teh-king.txt") == [f"Chapter {n}" for n in range(1, 82)]


def test_meditations_has_12_books() -> None:
    found = headings("marcus-aurelius/long-meditations.txt")
    assert all(re.fullmatch(r"Meditations \d+\.\d+", h) for h in found)
    assert {h.split()[1].split(".")[0] for h in found} == {str(n) for n in range(1, 13)}


def test_analects_has_20_books() -> None:
    found = headings("confucius/legge-analects.txt")
    assert all(re.fullmatch(r"Analects \d+\.\d+", h) for h in found)
    assert {h.split()[1].split(".")[0] for h in found} == {str(n) for n in range(1, 21)}


def test_enchiridion_chapter_count_matches_provenance() -> None:
    found = headings("epictetus/long-enchiridion.txt")
    assert found == [f"Enchiridion {n}" for n in range(1, len(found) + 1)]
    recorded = provenance_field("sources/epictetus/long-enchiridion.txt", "Structure")
    assert recorded.startswith(f"{len(found)} chapters")


def test_discourses_headings_are_book_and_chapter() -> None:
    found = headings("epictetus/long-discourses.txt")
    assert found and all(re.fullmatch(r"Discourses [1-4]\.\d+", h) for h in found)


def test_buddha_headings_are_citations() -> None:
    found = headings("buddha/sujato-suttas.txt")
    assert len(found) >= 100
    assert [h for h in found if not SUTTA_CITATION.match(h)] == []


@pytest.mark.parametrize("path", source_files(), ids=lambda p: str(p.relative_to(SOURCES)))
def test_every_source_file_is_listed_in_provenance_with_sha256(path: Path) -> None:
    relative = f"sources/{path.relative_to(SOURCES).as_posix()}"
    assert relative in provenance_sections(), f"{relative} has no section in PROVENANCE.md"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert provenance_field(relative, "sha256") == digest
    for field in (
        "Title",
        "Translator",
        "Published",
        "Licence basis",
        "Downloaded from",
        "Retrieved",
    ):
        assert provenance_field(relative, field)


@pytest.mark.parametrize("path", source_files(), ids=lambda p: str(p.relative_to(SOURCES)))
def test_headings_are_unique_within_a_file(path: Path) -> None:
    found = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("## ")
    ]
    assert found, "a source file needs at least one heading"
    assert len(found) == len(set(found))


@pytest.mark.parametrize("path", source_files(), ids=lambda p: str(p.relative_to(SOURCES)))
def test_no_distributor_boilerplate_is_committed(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "Project Gutenberg" not in text and "gutenberg.org" not in text


def test_the_five_public_domain_teachers_have_sources() -> None:
    expected = {
        "buddha/sujato-suttas.txt",
        "laozi/legge-tao-teh-king.txt",
        "confucius/legge-analects.txt",
        "marcus-aurelius/long-meditations.txt",
        "epictetus/long-enchiridion.txt",
        "epictetus/long-discourses.txt",
    }
    assert expected <= {p.relative_to(SOURCES).as_posix() for p in source_files()}
