"""The helpers every source build script uses."""

from pathlib import Path

import common
import pytest

GUTENBERG = """Title: Demo

*** START OF THE PROJECT GUTENBERG EBOOK DEMO ***

First paragraph of
the real text.

Second paragraph.

*** END OF THE PROJECT GUTENBERG EBOOK DEMO ***

Licence boilerplate.
"""


def test_strip_gutenberg_keeps_only_the_body() -> None:
    body = common.strip_gutenberg(GUTENBERG)
    assert body.startswith("First paragraph of")
    assert body.endswith("Second paragraph.")
    assert "Licence boilerplate" not in body and "Title: Demo" not in body


def test_strip_gutenberg_fails_without_markers() -> None:
    with pytest.raises(ValueError, match="START"):
        common.strip_gutenberg("no markers here")


def test_unchanged_words_pass() -> None:
    cleaned = (
        "## Chapter 1\n\nFirst paragraph of the real text.\n\n## Chapter 2\n\nSecond paragraph.\n"
    )
    common.assert_no_words_changed(GUTENBERG, cleaned)


def test_a_changed_word_is_caught() -> None:
    cleaned = "## Chapter 1\n\nFirst paragraph of the true text.\n"
    with pytest.raises(ValueError, match="true text"):
        common.assert_no_words_changed(GUTENBERG, cleaned)


def test_write_source_renders_headings_and_blocks(tmp_path: Path) -> None:
    out = tmp_path / "demo.txt"
    common.write_source(out, [("Chapter 1", "One.\n\nStill one."), ("Chapter 2", "Two.")])
    assert out.read_text(encoding="utf-8") == (
        "## Chapter 1\n\nOne.\n\nStill one.\n\n## Chapter 2\n\nTwo.\n"
    )


def test_write_source_refuses_duplicate_headings(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate heading"):
        common.write_source(tmp_path / "x.txt", [("A", "one"), ("A", "two")])


def test_record_provenance_replaces_its_own_section_only(tmp_path: Path) -> None:
    path = tmp_path / "PROVENANCE.md"
    path.write_text("# Provenance\n\nIntro.\n", encoding="utf-8")
    common.record_provenance(path, "sources/a/x.txt", {"Title": "X", "sha256": "111"})
    common.record_provenance(path, "sources/b/y.txt", {"Title": "Y", "sha256": "222"})
    common.record_provenance(path, "sources/a/x.txt", {"Title": "X", "sha256": "333"})
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Provenance\n\nIntro.\n")
    assert text.count("## sources/a/x.txt") == 1 and text.count("## sources/b/y.txt") == 1
    assert "- sha256: 333" in text and "- sha256: 111" not in text and "- sha256: 222" in text


def test_fetch_reads_from_the_cache_without_touching_the_network(tmp_path: Path) -> None:
    url = "https://example.invalid/never-fetched.txt"
    common.cache_path(url, tmp_path).write_bytes(b"cached bytes")
    assert common.fetch(url, tmp_path) == b"cached bytes"
