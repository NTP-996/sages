"""Re-checking remote-policy passages (and Jung's full editions) against their live sources."""

import json
from pathlib import Path
from typing import Any

import reverify_remote

PAGE = (
    "<html><head><style>p{color:red}</style><script>var x = 'Invert';</script></head><body>"
    "<h1>Commencement</h1><p>The safest way to try and get what you want is to try and "
    "<b>deserve</b> what you want.</p><p>It&rsquo;s such a simple idea.</p></body></html>"
)
URL = "https://example.org/usc-2007"


def remote(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "munger-deserve",
        "sage": "munger",
        "text": "safest way to try and get what you want is to try and deserve what you want.",
        "citation": "USC Law School commencement, 2007",
        "work": "USC Law School commencement address",
        "year": 2007,
        "source_title": "USC Law School commencement address",
        "source_url": URL,
        "checked": "2026-11-27",
        "themes": ["work"],
    }
    base.update(overrides)
    return base


def tree(tmp_path: Path, records: list[dict[str, Any]], sage: str = "munger") -> Path:
    skill = tmp_path / "skills" / sage
    skill.mkdir(parents=True, exist_ok=True)
    lines = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)
    (skill / "passages.jsonl").write_text(lines, encoding="utf-8")
    return tmp_path


def test_visible_text_drops_markup_scripts_and_styles() -> None:
    text = reverify_remote.visible_text(PAGE)
    assert "var x" not in text and "color:red" not in text
    assert "try and deserve what you want." in text
    assert "It’s such a simple idea." in text


def test_passage_on_the_page_passes(tmp_path: Path) -> None:
    assert reverify_remote.check_remote(tree(tmp_path, [remote()]), lambda url: PAGE) == (1, [])


def test_passage_not_on_the_page_fails_naming_it_and_the_url(tmp_path: Path) -> None:
    root = tree(tmp_path, [remote(text="Show me the incentive and I will show you the outcome.")])
    checked, problems = reverify_remote.check_remote(root, lambda url: PAGE)
    assert checked == 1 and len(problems) == 1
    assert "munger-deserve" in problems[0] and URL in problems[0]


def test_fetch_failure_is_reported_not_raised(tmp_path: Path) -> None:
    def broken(url: str) -> str:
        raise OSError("connection refused")

    _, problems = reverify_remote.check_remote(tree(tmp_path, [remote()]), broken)
    assert len(problems) == 1 and "could not fetch" in problems[0] and URL in problems[0]


def test_each_url_is_fetched_once(tmp_path: Path) -> None:
    calls: list[str] = []

    def counting(url: str) -> str:
        calls.append(url)
        return PAGE

    second = remote(id="munger-simple", text="such a simple idea.")
    assert reverify_remote.check_remote(tree(tmp_path, [remote(), second]), counting) == (2, [])
    assert calls == [URL]


def test_local_policy_passages_are_not_fetched(tmp_path: Path) -> None:
    local = {
        "id": "laozi-1",
        "sage": "laozi",
        "text": "x" * 30,
        "source_file": "sources/laozi/a.txt",
    }

    def never(url: str) -> str:
        raise AssertionError("a local-policy passage must not trigger a fetch")

    assert reverify_remote.check_remote(tree(tmp_path, [local], sage="laozi"), never) == (0, [])


def test_sage_filter_limits_what_is_checked(tmp_path: Path) -> None:
    root = tree(tmp_path, [remote()])
    assert reverify_remote.check_remote(root, lambda url: PAGE, sage="jung") == (0, [])
