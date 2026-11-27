"""The passage verifier: a quotation ships only if it is in its source, word for word."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import verify_passages

SCRIPT = Path(verify_passages.__file__)

SOURCE = """## Enchiridion 1
Of things some are in our power,
   and others are not.

## Enchiridion 5
Men are disturbed not by the things which happen,
but by the opinions about the things.

## Dhp 277
“All conditions are impermanent”—when this is seen with wisdom
"""


def record(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "epictetus-ench-1",
        "sage": "epictetus",
        "text": "Of things some are in our power, and others are not.",
        "citation": "Enchiridion 1",
        "work": "Enchiridion",
        "translator": "George Long",
        "year": 1877,
        "source_file": "sources/epictetus/long.txt",
        "under_heading": "Enchiridion 1",
        "themes": ["freedom"],
    }
    base.update(overrides)
    return base


def remote_record(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "munger-invert",
        "sage": "munger",
        "text": "Invert, always invert: turn a situation or problem upside down.",
        "citation": "Harvard School commencement, 1986",
        "work": "Harvard School commencement address",
        "year": 1986,
        "source_title": "Harvard School commencement address",
        "source_url": "https://example.org/munger-1986",
        "checked": "2026-11-27",
        "themes": ["learning"],
    }
    base.update(overrides)
    return base


def make_tree(tmp_path: Path, records: list[dict[str, Any]], sage: str = "epictetus") -> Path:
    (tmp_path / "sources" / "epictetus").mkdir(parents=True, exist_ok=True)
    (tmp_path / "sources" / "epictetus" / "long.txt").write_text(SOURCE, encoding="utf-8")
    skill = tmp_path / "skills" / sage
    skill.mkdir(parents=True, exist_ok=True)
    lines = "\n".join(json.dumps(item, ensure_ascii=False) for item in records)
    (skill / "passages.jsonl").write_text(lines + "\n", encoding="utf-8")
    return tmp_path


def problems(tmp_path: Path, records: list[dict[str, Any]], sage: str = "epictetus") -> list[str]:
    return verify_passages.check_passages(make_tree(tmp_path, records, sage))


def test_verbatim_passage_passes(tmp_path: Path) -> None:
    assert problems(tmp_path, [record()]) == []


def test_fabricated_passage_fails(tmp_path: Path) -> None:
    fake = record(text="It's not what happens to you, but how you react to it that matters.")
    found = problems(tmp_path, [fake])
    assert len(found) == 1
    assert "not found verbatim" in found[0]
    assert "epictetus-ench-1" in found[0]


def test_wrong_heading_fails(tmp_path: Path) -> None:
    found = problems(tmp_path, [record(under_heading="Enchiridion 5")])
    assert len(found) == 1
    assert "Enchiridion 1" in found[0] and "Enchiridion 5" in found[0]


def test_a_line_repeated_under_two_headings_is_checked_under_the_one_named(tmp_path: Path) -> None:
    twice = (
        "## Enchiridion 1\nIt is not things that disturb us.\n\n"
        "## Enchiridion 5\nIt is not things that disturb us.\n"
    )

    def check(heading: str) -> list[str]:
        line = record(text="It is not things that disturb us.", under_heading=heading)
        root = make_tree(tmp_path, [line])
        (root / "sources" / "epictetus" / "long.txt").write_text(twice, encoding="utf-8")
        return verify_passages.check_passages(root)

    assert check("Enchiridion 5") == []
    found = check("Enchiridion 9")
    assert len(found) == 1 and "Enchiridion 9" in found[0]


def test_whitespace_differences_pass(tmp_path: Path) -> None:
    spaced = record(text="Of things some are in our power,\n\tand   others are not.")
    assert problems(tmp_path, [spaced]) == []


def test_verifies_non_ascii_passage(tmp_path: Path) -> None:
    pali = record(
        id="epictetus-dhp-277",
        text="“All conditions are impermanent”—when this is seen with wisdom",
        citation="Dhp 277",
        under_heading="Dhp 277",
    )
    assert problems(tmp_path, [pali]) == []


def test_punctuation_difference_fails(tmp_path: Path) -> None:
    straightened = record(
        id="epictetus-dhp-277",
        text='"All conditions are impermanent"-when this is seen with wisdom',
        citation="Dhp 277",
        under_heading="Dhp 277",
    )
    found = problems(tmp_path, [straightened])
    assert len(found) == 1 and "not found verbatim" in found[0]


def test_duplicate_id_fails(tmp_path: Path) -> None:
    found = problems(tmp_path, [record(), record()])
    assert any("duplicate id" in problem for problem in found)


def test_id_must_start_with_the_sage(tmp_path: Path) -> None:
    found = problems(tmp_path, [record(id="marcus-ench-1")])
    assert any("must start with 'epictetus-'" in problem for problem in found)


def test_sage_must_match_the_skill_folder(tmp_path: Path) -> None:
    found = problems(tmp_path, [record()], sage="laozi")
    assert any("does not match the skill folder 'laozi'" in problem for problem in found)


def test_local_sage_without_source_file_fails(tmp_path: Path) -> None:
    orphan = record()
    del orphan["source_file"]
    found = problems(tmp_path, [orphan])
    assert any("missing field 'source_file'" in problem for problem in found)


def test_source_file_outside_sources_dir_fails(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir(parents=True, exist_ok=True)
    (tmp_path / "secret.txt").write_text(SOURCE, encoding="utf-8")
    found = problems(tmp_path, [record(source_file="sources/../secret.txt")])
    assert any("is not a file under sources/" in problem for problem in found)


def test_remote_sage_passes_with_url_title_and_checked_date(tmp_path: Path) -> None:
    assert problems(tmp_path, [remote_record()], sage="munger") == []


def test_remote_sage_requires_url_title_and_checked_date(tmp_path: Path) -> None:
    bare = remote_record()
    for field in ("source_title", "source_url", "checked"):
        del bare[field]
    found = problems(tmp_path, [bare], sage="munger")
    assert {"source_title", "source_url", "checked"} <= {
        name for name in ("source_title", "source_url", "checked") if any(name in p for p in found)
    }


def test_remote_url_must_be_https(tmp_path: Path) -> None:
    found = problems(tmp_path, [remote_record(source_url="http://example.org/x")], sage="munger")
    assert any("https://" in problem for problem in found)


def test_remote_passage_longer_than_300_chars_fails(tmp_path: Path) -> None:
    long_text = "Take a simple idea and take it seriously. " * 8
    found = problems(tmp_path, [remote_record(text=long_text)], sage="munger")
    assert any("300" in problem for problem in found)


def test_remote_sage_may_not_name_a_source_file(tmp_path: Path) -> None:
    sneaky = remote_record(source_file="sources/epictetus/long.txt")
    found = problems(tmp_path, [sneaky], sage="munger")
    assert any("must not carry source_file" in problem for problem in found)


def test_unknown_sage_has_no_policy(tmp_path: Path) -> None:
    found = problems(tmp_path, [record(id="seneca-1", sage="seneca")], sage="seneca")
    assert any("no source policy" in problem for problem in found)


def test_invalid_json_line_is_reported_with_its_line_number(tmp_path: Path) -> None:
    root = make_tree(tmp_path, [record()])
    path = root / "skills" / "epictetus" / "passages.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "{not json}\n", encoding="utf-8")
    found = verify_passages.check_passages(root)
    assert any("line 2" in problem and "not valid JSON" in problem for problem in found)


def test_cli_exits_zero_and_reports_the_count_when_clean(tmp_path: Path) -> None:
    root = make_tree(tmp_path, [record()])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "1 passage verified" in result.stdout


def test_cli_exits_one_and_prints_each_problem(tmp_path: Path) -> None:
    root = make_tree(tmp_path, [record(text="These words are in no source at all.")])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "not found verbatim" in result.stdout


def test_a_tree_with_no_passages_is_a_failure(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "no passages found" in result.stdout
