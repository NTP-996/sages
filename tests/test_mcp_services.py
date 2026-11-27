"""Business logic of the MCP server, against an in-memory repository."""

import pytest

from sages_mcp.models import Passage, Sage
from sages_mcp.services import PassageService, SageService, UnknownSageError

ROSTER = (
    Sage("laozi", "Laozi", ("lao tzu", "lao-tzu"), "6th c. BCE", "Taoism", "Stop forcing."),
    Sage(
        "epictetus", "Epictetus", ("epiktetos",), "c. 50-135", "Stoicism", "Sort what is up to you."
    ),
    Sage(
        "marcus-aurelius",
        "Marcus Aurelius",
        ("marcus",),
        "121-180",
        "Stoicism",
        "Do the day's duty.",
    ),
)
ENCH5 = Passage(
    id="epictetus-ench-5",
    sage="epictetus",
    text="Men are disturbed not by the things which happen, but by the opinions about the things",
    citation="Enchiridion 5",
    work="Enchiridion",
    themes=("anxiety", "the-self"),
    translator="George Long",
    year=1877,
)
ENCH8 = Passage(
    id="epictetus-ench-8",
    sage="epictetus",
    text="Seek not that the things which happen should happen as you wish; but wish the things which happen to be as they are, and you will have a tranquil flow of life.",
    citation="Enchiridion 8",
    work="Enchiridion",
    themes=("contentment",),
)
WATER = Passage(
    id="laozi-8-water",
    sage="laozi",
    text="The highest excellence is like (that of) water.",
    citation="Tao Te Ching 8",
    work="Tao Te Ching",
    themes=("nature", "humility"),
)
SWARM = Passage(
    id="marcus-aurelius-6-54",
    sage="marcus-aurelius",
    text="That which is not good for the swarm, neither is it good for the bee.",
    citation="Meditations 6.54",
    work="Meditations",
    themes=("duty",),
)


class FakeSages:
    def roster(self) -> tuple[Sage, ...]:
        return ROSTER

    def skill_body(self, skill: str) -> str:
        return f"# {skill}\n\nSpeak as {skill}."

    def passages(self, sage_id: str) -> tuple[Passage, ...]:
        return tuple(p for p in (WATER, ENCH5, ENCH8, SWARM) if p.sage == sage_id)


class FakeSources:
    """Pretends the bundled text of Epictetus has one more line under Enchiridion 9."""

    def search(self, loose_text: str, sage_id: str | None) -> tuple[str, str] | None:
        if "lameness is an impediment to the leg" in loose_text and sage_id in (None, "epictetus"):
            return ("epictetus", "Enchiridion 9")
        return None


@pytest.fixture
def sages() -> SageService:
    return SageService(FakeSages())


@pytest.fixture
def passages(sages: SageService) -> PassageService:
    return PassageService(FakeSages(), FakeSources(), sages)


def test_lists_the_roster_in_council_order(sages: SageService) -> None:
    assert [sage.id for sage in sages.list()] == ["laozi", "epictetus", "marcus-aurelius"]


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("Marcus Aurelius", "marcus-aurelius"),
        ("marcus", "marcus-aurelius"),
        ("marcus_aurelius", "marcus-aurelius"),
        (" EPICTETUS ", "epictetus"),
        ("Lao Tzu", "laozi"),
        ("lao-tzu", "laozi"),
        ("laozi", "laozi"),
    ],
)
def test_resolves_aliases(sages: SageService, given: str, expected: str) -> None:
    assert sages.resolve(given).id == expected


def test_unknown_sage_lists_valid_ids(sages: SageService) -> None:
    with pytest.raises(UnknownSageError) as error:
        sages.resolve("Seneca")
    message = str(error.value)
    assert "Seneca" in message
    assert all(sage.id in message for sage in ROSTER)


def test_persona_carries_instructions_and_passage_count(sages: SageService) -> None:
    persona = sages.persona("epiktetos")
    assert persona.sage.id == "epictetus"
    assert persona.instructions == "# epictetus\n\nSpeak as epictetus."
    assert persona.passage_count == 2


def test_council_defaults_to_everyone_in_order(sages: SageService) -> None:
    brief = sages.council("Should I take the job?", None)
    assert [voice.sage.id for voice in brief.voices] == ["laozi", "epictetus", "marcus-aurelius"]
    assert brief.question == "Should I take the job?" and brief.protocol.startswith(
        "# sage-council"
    )


def test_council_subset_keeps_council_order_and_drops_duplicates(sages: SageService) -> None:
    brief = sages.council("x?", ["marcus", "Lao Tzu", "Marcus Aurelius"])
    assert [voice.sage.id for voice in brief.voices] == ["laozi", "marcus-aurelius"]


def test_council_needs_a_question(sages: SageService) -> None:
    with pytest.raises(ValueError, match="question"):
        sages.council("   ", None)


def test_find_by_sage_theme_and_query(passages: PassageService) -> None:
    assert [p.id for p in passages.find(sage="Epictetus")] == [
        "epictetus-ench-5",
        "epictetus-ench-8",
    ]
    assert [p.id for p in passages.find(theme="DUTY")] == ["marcus-aurelius-6-54"]
    assert [p.id for p in passages.find(query="opinions disturbed")] == ["epictetus-ench-5"]
    assert [p.id for p in passages.find(query="enchiridion 8")] == ["epictetus-ench-8"]
    assert passages.find(sage="laozi", theme="duty") == ()


def test_find_with_no_filter_returns_passages_from_every_teacher(passages: PassageService) -> None:
    assert {p.sage for p in passages.find(limit=20)} == {"laozi", "epictetus", "marcus-aurelius"}


@pytest.mark.parametrize(("limit", "expected"), [(0, 1), (-3, 1), (2, 2), (500, 4)])
def test_limit_is_clamped(passages: PassageService, limit: int, expected: int) -> None:
    assert len(passages.find(limit=limit)) == expected


def test_themes_are_counted(passages: PassageService) -> None:
    themes = passages.themes()
    assert themes["duty"] == 1 and themes["anxiety"] == 1
    assert list(themes) == sorted(themes, key=lambda theme: (-themes[theme], theme))


def test_exact_quote_is_verified(passages: PassageService) -> None:
    check = passages.verify_quote(
        "men are disturbed not by the things which happen, but by the opinions about the things.",
        None,
    )
    assert check.status == "verified"
    assert [p.id for p in check.matches] == ["epictetus-ench-5"]


def test_part_of_a_passage_is_verified(passages: PassageService) -> None:
    check = passages.verify_quote("wish the things which happen to be as they are", "epictetus")
    assert check.status == "verified" and check.matches[0].citation == "Enchiridion 8"


def test_fake_quote_is_not_verified(passages: PassageService) -> None:
    check = passages.verify_quote(
        "It's not what happens to you, but how you react to it that matters.", "epictetus"
    )
    assert check.status == "not-found"
    assert check.matches == ()
    assert "quotation marks" in check.note


def test_near_paraphrase_returns_close_with_genuine_wording(passages: PassageService) -> None:
    check = passages.verify_quote(
        "Men are disturbed not by things which happen but by their opinions about the things", None
    )
    assert check.status == "close"
    assert check.matches[0].text == ENCH5.text


def test_a_genuine_line_padded_with_extra_words_is_only_close(passages: PassageService) -> None:
    padded = "That which is not good for the swarm, neither is it good for the bee, so hustle harder every day."
    assert passages.verify_quote(padded, None).status in {"close", "not-found"}


def test_line_found_only_in_the_bundled_source_is_in_source(passages: PassageService) -> None:
    check = passages.verify_quote(
        "Lameness is an impediment to the leg, but not to the will.", None
    )
    assert check.status == "in-source"
    assert check.source_citation == "Enchiridion 9" and "epictetus" in check.note.lower()


def test_too_short_to_check(passages: PassageService) -> None:
    check = passages.verify_quote("Know thyself", None)
    assert check.status == "not-found" and "six words" in check.note


def test_verify_quote_with_unknown_sage_raises(passages: PassageService) -> None:
    with pytest.raises(UnknownSageError):
        passages.verify_quote("some six word line goes right here", "seneca")
