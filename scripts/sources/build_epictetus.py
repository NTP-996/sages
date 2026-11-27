#!/usr/bin/env python3
"""Build the two Epictetus sources from the English Wikisource transcription.

George Long's translation, "The Discourses of Epictetus; with the Encheiridion and
Fragments" (1877). Wikisource holds a proofread transcription, one page per chapter. This
script reads the rendered pages, keeps the text of the translation, and drops Long's
footnotes and their reference marks, the page numbers and the navigation.

* sources/epictetus/long-enchiridion.txt - one "## Enchiridion N" heading per chapter, in
  the numbering of this translation.
* sources/epictetus/long-discourses.txt  - one "## Discourses B.C" heading per chapter; the
  first line under a heading is Long's chapter title.

Usage: python scripts/sources/build_epictetus.py --root .
"""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

import common

BASE = (
    "https://en.wikisource.org/w/index.php?title="
    "The_Discourses_of_Epictetus%3B_with_the_Encheiridion_and_Fragments/{page}&action=render"
)
ENCHIRIDION_URL = BASE.format(page="The_Encheiridion_or_Manual")
CHAPTERS_PER_BOOK = (30, 26, 26, 13)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
ROMAN_LINE = re.compile(r"^([IVXLC]+)\.$")
ZERO_WIDTH = "​"


def roman_to_int(roman: str) -> int:
    total = 0
    for index, char in enumerate(roman):
        value = ROMAN_VALUES[char]
        if index + 1 < len(roman) and ROMAN_VALUES[roman[index + 1]] > value:
            total -= value
        else:
            total += value
    return total


def _classes(attrs: list[tuple[str, str | None]]) -> str:
    return next((value or "" for name, value in attrs if name == "class"), "")


def _is_skipped(tag: str, classes: str) -> bool:
    return (
        tag in {"sup", "style"}
        or (tag == "span" and "pagenum" in classes)
        or (tag == "div" and "ws-noexport" in classes)
    )


class _Extractor(HTMLParser):
    """Collect ("p" | "center", text) blocks from the transcription, up to the footnotes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []
        self._stack: list[tuple[str, str]] = []  # (tag, role)
        self._buffer: list[str] = []
        self._kind = "p"
        self._done = False

    def _depth(self, role: str) -> int:
        return sum(1 for _, r in self._stack if r == role)

    def _flush(self) -> None:
        text = "".join(self._buffer).replace(ZERO_WIDTH, "")
        lines = [common.normalise(line) for line in text.split("\n")]
        text = "\n".join(line for line in lines if line)
        if text:
            self.blocks.append((self._kind, text))
        self._buffer = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._done:
            return
        classes = _classes(attrs)
        if tag == "br":
            self._buffer.append("\n")
        if tag in VOID:
            return
        role = ""
        if tag == "div" and "prp-pages-output" in classes:
            role = "output"
        elif _is_skipped(tag, classes):
            role = "skip"
        elif tag == "h2" and self._depth("output"):
            self._flush()
            self._done = True
            return
        elif tag == "div" and "wst-center" in classes:
            role = "center"
            if not self._depth("center"):
                self._flush()
                self._kind = "center"
        elif tag == "p":
            if self._depth("center"):
                self._buffer.append("\n")
            else:
                self._flush()
                self._kind = "p"
        self._stack.append((tag, role))

    def handle_endtag(self, tag: str) -> None:
        if self._done or tag in VOID:
            return
        while self._stack:
            opened, role = self._stack.pop()
            if role == "center" and not self._depth("center"):
                self._flush()
                self._kind = "p"
            if opened == tag:
                break
        if tag == "p" and not self._depth("center"):
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._done or not self._depth("output") or self._depth("skip"):
            return
        self._buffer.append(data)


class _Flat(HTMLParser):
    """The same text with no block logic: what the extractor's blocks are checked against."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._stack: list[tuple[str, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self.parts.append("\n")
        if tag not in VOID:
            self._stack.append((tag, _is_skipped(tag, _classes(attrs))))
        if tag in {"p", "div"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        while self._stack and self._stack.pop()[0] != tag:
            pass
        if tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not any(skipped for _, skipped in self._stack):
            self.parts.append(data.replace(ZERO_WIDTH, ""))


def extract(html: str) -> list[tuple[str, str]]:
    parser = _Extractor()
    parser.feed(html)
    parser.close()
    return parser.blocks


def flat_text(html: str) -> str:
    parser = _Flat()
    parser.feed(html)
    parser.close()
    return "".join(parser.parts)


def enchiridion(html: str) -> list[tuple[str, str]]:
    chapters: list[tuple[str, list[str]]] = []
    for kind, text in extract(html):
        numeral = ROMAN_LINE.match(text) if kind == "center" else None
        if numeral:
            number = roman_to_int(numeral.group(1))
            if number != len(chapters) + 1:
                raise ValueError(f"Enchiridion chapter {numeral.group(1)} is out of order")
            chapters.append((f"Enchiridion {number}", []))
        elif chapters:
            chapters[-1][1].append(text)
    return [(heading, "\n\n".join(parts)) for heading, parts in chapters]


def discourse(html: str, book: int, chapter: int) -> tuple[str, str]:
    parts = [
        text
        for kind, text in extract(html)
        if not (kind == "center" and re.fullmatch(r"(BOOK|CHAPTER) [IVXLC]+\.", text))
    ]
    if not parts:
        raise ValueError(f"Discourses {book}.{chapter}: no text extracted")
    return f"Discourses {book}.{chapter}", "\n\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--cache", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    cache = Path(args.cache or root / "sources-local" / "cache")
    shared = {
        "Translator": "George Long (1800-1879)",
        "Published": "1877",
        "Licence basis": "public domain worldwide (the translator died in 1879)",
        "Retrieved": "2026-11-27",
        "Removed": "Long's footnotes and their reference marks, page numbers, navigation",
    }

    html = common.decode(common.fetch(ENCHIRIDION_URL, cache))
    chapters = enchiridion(html)
    common.finish(
        root / "sources/epictetus/long-enchiridion.txt",
        flat_text(html),
        chapters,
        root,
        {
            "Title": "The Encheiridion, or Manual, of Epictetus",
            **shared,
            "Downloaded from": f"{ENCHIRIDION_URL} (English Wikisource, proofread transcription)",
            "Inserted": "one '## Enchiridion N' heading per chapter, in this translation's numbering",
            "Structure": f"{len(chapters)} chapters",
        },
    )

    blocks: list[tuple[str, str]] = []
    flat: list[str] = []
    for book, count in enumerate(CHAPTERS_PER_BOOK, start=1):
        for chapter in range(1, count + 1):
            url = BASE.format(page=f"Book_{book}/Chapter_{chapter}")
            html = common.decode(common.fetch(url, cache))
            flat.append(flat_text(html))
            blocks.append(discourse(html, book, chapter))
    common.finish(
        root / "sources/epictetus/long-discourses.txt",
        "\n".join(flat),
        blocks,
        root,
        {
            "Title": "The Discourses of Epictetus, as recorded by Arrian",
            **shared,
            "Downloaded from": BASE.format(page="Book_<b>/Chapter_<c>")
            + " for each chapter (English Wikisource, proofread transcription)",
            "Inserted": "one '## Discourses B.C' heading per chapter; the line after it is "
            "Long's chapter title",
            "Structure": f"4 books, {len(blocks)} chapters; chapters per book "
            f"{list(CHAPTERS_PER_BOOK)}",
        },
    )


if __name__ == "__main__":
    main()
