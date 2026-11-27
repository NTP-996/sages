"""The filesystem repositories and the settings that locate the content."""

from pathlib import Path

import pytest

from sages_mcp.config import settings
from sages_mcp.repositories import FileSageRepository, FileSourceRepository
from sages_mcp.utils.text import loose

ROOT = Path(__file__).resolve().parents[1]


def test_roster_and_passages_are_read_from_the_skills_tree() -> None:
    repository = FileSageRepository(ROOT)
    assert [sage.id for sage in repository.roster()][:2] == ["laozi", "buddha"]
    passages = repository.passages("munger")
    assert len(passages) >= 20 and passages[0].source_url and passages[0].translator is None
    assert repository.passages("nobody") == ()


def test_skill_body_drops_the_frontmatter() -> None:
    body = FileSageRepository(ROOT).skill_body("epictetus")
    assert body.startswith("# Epictetus") and "description:" not in body.split("\n")[0]


@pytest.mark.parametrize("name", ["seneca", "epictetus/evals", "..\\x"])
def test_unknown_or_unsafe_skill_names_are_refused(name: str) -> None:
    with pytest.raises(KeyError):
        FileSageRepository(ROOT).skill_body(name)


def test_source_search_finds_the_section_and_respects_the_teacher() -> None:
    sources = FileSourceRepository(ROOT)
    needle = loose("Seek not that the things which happen should happen as you wish")
    assert sources.search(needle, None) == ("epictetus", "Enchiridion 8")
    assert sources.search(needle, "laozi") is None
    assert sources.search("", None) is None
    assert sources.search(loose("a sentence that is in no source text whatsoever"), None) is None


def test_data_dir_prefers_the_environment_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "skills" / "sages").mkdir(parents=True)
    (tmp_path / "skills" / "sages" / "roster.json").write_text("[]", encoding="utf-8")
    monkeypatch.setenv(settings.ENV_DATA_DIR, str(tmp_path))
    assert settings.data_dir() == tmp_path


def test_data_dir_falls_back_to_the_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(settings.ENV_DATA_DIR, raising=False)
    assert (settings.data_dir() / "skills" / "sages" / "roster.json").is_file()


def test_data_dir_says_where_it_looked_when_nothing_is_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "_PACKAGE", tmp_path / "a" / "b" / "c")
    monkeypatch.delenv(settings.ENV_DATA_DIR, raising=False)
    with pytest.raises(RuntimeError, match="SAGES_DATA_DIR"):
        settings.data_dir()
