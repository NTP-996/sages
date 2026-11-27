"""The quote guard: no quotation enters a skill unless it is a verified passage."""

import json
from pathlib import Path

import quote_guard

RECORD = {
    "id": "epictetus-ench-5",
    "sage": "epictetus",
    "text": "Men are disturbed not by the things which happen, but by the opinions about the things",
    "citation": "Enchiridion 5",
}
LISTED = f'- "{RECORD["text"]}" — {RECORD["citation"]}'


def make_skill(tmp_path: Path, body: str, records: list[dict[str, str]] | None = None) -> Path:
    skill = tmp_path / "skills" / "epictetus"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: epictetus\ndescription: test\n---\n# Epictetus\n\n{body}\n", encoding="utf-8"
    )
    if records is not None:
        lines = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)
        (skill / "passages.jsonl").write_text(lines, encoding="utf-8")
    return tmp_path


def test_listed_passage_that_matches_a_record_passes(tmp_path: Path) -> None:
    root = make_skill(tmp_path, f"## Passages\n\n{LISTED}\n\n## Limits\n\nNone.", [RECORD])
    assert quote_guard.find_problems(root) == []


def test_listed_passage_must_match_a_record(tmp_path: Path) -> None:
    body = '## Passages\n\n- "It is not what happens to you, but how you react to it that matters." — Enchiridion 5'
    problems = quote_guard.find_problems(make_skill(tmp_path, body, [RECORD]))
    assert len(problems) == 1 and "not a verified passage" in problems[0]


def test_citation_mismatch_fails(tmp_path: Path) -> None:
    body = f'## Passages\n\n- "{RECORD["text"]}" — Enchiridion 9'
    problems = quote_guard.find_problems(make_skill(tmp_path, body, [RECORD]))
    assert len(problems) == 1 and "Enchiridion 5" in problems[0] and "Enchiridion 9" in problems[0]


def test_malformed_passage_item_fails(tmp_path: Path) -> None:
    body = f"## Passages\n\n- {RECORD['text']} (Enchiridion 5)"
    problems = quote_guard.find_problems(make_skill(tmp_path, body, [RECORD]))
    assert len(problems) == 1 and "must be written" in problems[0]


def test_long_unverified_quote_outside_passages_fails(tmp_path: Path) -> None:
    body = '## How he talks\n\nHe says "it is not what happens to you but how you react that matters" a lot.'
    problems = quote_guard.find_problems(make_skill(tmp_path, body, [RECORD]))
    assert len(problems) == 1 and "unverified quotation" in problems[0]


def test_curly_quotes_are_checked_too(tmp_path: Path) -> None:
    body = "## How he talks\n\nHe says “it is not what happens to you but how you react that matters” a lot."
    assert len(quote_guard.find_problems(make_skill(tmp_path, body, [RECORD]))) == 1


def test_short_quoted_phrase_is_allowed(tmp_path: Path) -> None:
    body = '## How he talks\n\nUse when the user says "talk to Laozi" or "ask the sages".'
    assert quote_guard.find_problems(make_skill(tmp_path, body, [RECORD])) == []


def test_a_verified_passage_may_be_quoted_anywhere(tmp_path: Path) -> None:
    body = f'## How he talks\n\nHe opens with "{RECORD["text"]}" and waits.'
    assert quote_guard.find_problems(make_skill(tmp_path, body, [RECORD])) == []


def test_a_skill_without_passages_may_not_quote_at_length(tmp_path: Path) -> None:
    body = 'The council says "one question asked of all the teachers and answered by each in turn" here.'
    assert len(quote_guard.find_problems(make_skill(tmp_path, body, None))) == 1


def test_cli_exit_codes(tmp_path: Path) -> None:
    clean = make_skill(tmp_path / "a", f"## Passages\n\n{LISTED}", [RECORD])
    dirty = make_skill(
        tmp_path / "b",
        '## Passages\n\n- "A line nobody ever recorded anywhere at all." — x',
        [RECORD],
    )
    assert quote_guard.main(["--root", str(clean)]) == 0
    assert quote_guard.main(["--root", str(dirty)]) == 1
