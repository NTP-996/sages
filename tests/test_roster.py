"""The roster, the front door and the council agree on who the teachers are."""

import json
import re
from pathlib import Path

from test_skills import PERSONAS, split

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
COUNCIL_ORDER = ("laozi", "buddha", "confucius", "epictetus", "marcus-aurelius", "jung", "munger")
ALL_SKILLS = {*PERSONAS, "sages", "sage-council"}
FIELDS = {"id", "name", "aliases", "era", "tradition", "one_line", "hermes_profile"}
HERMES_PROFILES = {
    "laozi": "laozi",
    "buddha": "buddha",
    "confucius": "confucius",
    "epictetus": "epictetus",
    "marcus-aurelius": "marcus",
    "jung": "jung",
    "munger": "munger",
}


def roster() -> list[dict[str, object]]:
    data = json.loads((SKILLS / "sages" / "roster.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)
    return data


def test_all_nine_skills_exist() -> None:
    assert {p.name for p in SKILLS.iterdir() if p.is_dir()} == ALL_SKILLS


def test_roster_matches_persona_folders_in_council_order() -> None:
    assert tuple(entry["id"] for entry in roster()) == COUNCIL_ORDER
    assert set(COUNCIL_ORDER) == set(PERSONAS)


def test_roster_entries_have_every_field() -> None:
    for entry in roster():
        assert set(entry) == FIELDS, entry.get("id")
        assert all(entry[key] for key in FIELDS), entry.get("id")
        assert len(str(entry["one_line"])) <= 120


def test_hermes_profile_names() -> None:
    assert {str(e["id"]): e["hermes_profile"] for e in roster()} == HERMES_PROFILES


def test_aliases_are_unique_across_teachers() -> None:
    seen: dict[str, str] = {}
    for entry in roster():
        aliases = entry["aliases"]
        assert isinstance(aliases, list)
        for alias in [str(entry["id"]), *aliases]:
            assert alias == alias.lower().strip(), f"{alias!r} must be lower case"
            assert alias not in seen, f"{alias!r} names both {seen.get(alias)} and {entry['id']}"
            seen[alias] = str(entry["id"])


def test_front_door_names_every_teacher() -> None:
    _, body = split("sages")
    for entry in roster():
        assert str(entry["name"]) in body, entry["id"]
        assert f"`{entry['id']}`" in body, entry["id"]
    assert "`sage-council`" in body


def test_council_names_every_teacher_in_order() -> None:
    _, body = split("sage-council")
    names = [str(entry["name"]) for entry in roster()]
    order_line = next(line for line in body.splitlines() if all(name in line for name in names))
    assert [order_line.index(name) for name in names] == sorted(order_line.index(n) for n in names)
    for skill in COUNCIL_ORDER:
        assert f"`{skill}`" in body


def test_council_keeps_the_teachers_apart() -> None:
    _, body = split("sage-council")
    assert re.search(r"^## .*part", body, re.MULTILINE | re.IGNORECASE)
    assert "no investment advice" in body and "no diagnosis" in body


def test_front_door_and_council_word_budgets() -> None:
    assert len(split("sages")[1].split()) <= 400
    assert len(split("sage-council")[1].split()) <= 700
