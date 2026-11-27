"""Every shipped skill is well formed, and the seven portrayals keep their shared shape."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
PERSONAS: tuple[str, ...] = (
    "buddha",
    "laozi",
    "confucius",
    "marcus-aurelius",
    "epictetus",
    "jung",
    "munger",
)
SECTIONS = (
    "Who is speaking",
    "How he talks",
    "What he teaches",
    "How he meets a question",
    "Passages",
    "Ground rules for this portrayal",
    "Limits",
)
CONTRACT = re.compile(
    r"<!-- portrayal-contract:start -->\n(.*?)\n<!-- portrayal-contract:end -->", re.DOTALL
)
FRONTMATTER_MAX = 1024
PERSONA_WORD_BUDGET = 1600
FILE_REFERENCE = re.compile(r"`([\w./-]+\.(?:md|jsonl|json|txt|py|sh|yaml))`")


def skill_dirs() -> list[Path]:
    return sorted(p for p in SKILLS.iterdir() if p.is_dir())


def read(skill: str) -> str:
    return (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")


def split(skill: str) -> tuple[str, str]:
    """Return (frontmatter, body) of a skill."""
    text = read(skill)
    assert text.startswith("---\n"), f"{skill}: SKILL.md has no frontmatter"
    end = text.index("\n---\n", 4)
    return text[4 : end + 1], text[end + 5 :]


def field(frontmatter: str, key: str) -> str | None:
    for line in frontmatter.splitlines():
        if line.startswith(f"{key}:"):
            value = line[len(key) + 1 :].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            return value
    return None


def test_the_seven_portrayals_exist() -> None:
    assert set(PERSONAS) <= {p.name for p in skill_dirs()}


@pytest.mark.parametrize("skill", [p.name for p in skill_dirs()])
def test_frontmatter_valid(skill: str) -> None:
    frontmatter, _ = split(skill)
    assert len(frontmatter) <= FRONTMATTER_MAX, f"{skill}: frontmatter is {len(frontmatter)} chars"
    assert field(frontmatter, "name") == skill
    assert field(frontmatter, "description")
    assert set(re.findall(r"^(\w[\w-]*):", frontmatter, re.MULTILINE)) == {"name", "description"}


@pytest.mark.parametrize("skill", [p.name for p in skill_dirs()])
def test_no_parent_directory_steps(skill: str) -> None:
    assert "../" not in read(skill)


@pytest.mark.parametrize("skill", PERSONAS)
def test_persona_sections_in_order(skill: str) -> None:
    _, body = split(skill)
    assert tuple(re.findall(r"^## (.+)$", body, re.MULTILINE)) == SECTIONS


def test_contract_identical_in_all_seven() -> None:
    contracts = {skill: CONTRACT.search(read(skill)) for skill in PERSONAS}
    assert all(contracts.values()), "every portrayal carries the contract block"
    texts = {match.group(1) for match in contracts.values() if match}
    assert len(texts) == 1, "the contract block must be byte-identical in the seven portrayals"
    (only,) = texts
    assert only.startswith("## Ground rules for this portrayal\n")
    for promise in (
        "AI portrayal",
        "Never invent a quotation",
        "Step out of the voice",
        "drop the voice",
    ):
        assert promise in only


@pytest.mark.parametrize("skill", PERSONAS)
def test_persona_word_budget(skill: str) -> None:
    _, body = split(skill)
    assert len(body.split()) <= PERSONA_WORD_BUDGET


@pytest.mark.parametrize("skill", PERSONAS)
def test_persona_skill_is_self_contained(skill: str) -> None:
    """A registry may install one portrayal folder alone: it may name no file but its own data."""
    assert set(FILE_REFERENCE.findall(read(skill))) <= {"passages.jsonl"}
    assert (SKILLS / skill / "passages.jsonl").is_file()
    assert "skills/" not in read(skill)


@pytest.mark.parametrize("skill", PERSONAS)
def test_description_names_when_not_to_use(skill: str) -> None:
    frontmatter, _ = split(skill)
    description = field(frontmatter, "description") or ""
    assert "Use when" in description and "Not for" in description


@pytest.mark.parametrize("skill", PERSONAS)
def test_persona_lists_ten_to_twelve_passages(skill: str) -> None:
    _, body = split(skill)
    section = body.split("## Passages\n", 1)[1].split("\n## ", 1)[0]
    assert 10 <= len(re.findall(r"^- ", section, re.MULTILINE)) <= 12


def test_jung_states_he_is_not_an_analyst() -> None:
    text = read("jung")
    assert "You are not their analyst" in text
    assert "never a diagnosis" in text and "Myers-Briggs" in text


def test_munger_states_no_investment_advice() -> None:
    text = read("munger")
    assert "This is not investment advice" in text
    assert "November 2023" in text and "not endorsed" in text


def test_epictetus_never_offers_the_open_door() -> None:
    assert "Never offer this to anyone" in read("epictetus")
