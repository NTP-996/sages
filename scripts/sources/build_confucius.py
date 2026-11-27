#!/usr/bin/env python3
"""Build sources/confucius/legge-analects.txt from Project Gutenberg ebook 3330.

James Legge's translation of the Confucian Analects (The Chinese Classics, vol. 1, 1861;
revised 1893). The download prints twenty "BOOK <roman>." lines, labels chapters
"CHAPTER I." / "CHAP. II.", and numbers the paragraphs inside a chapter. This script gives
every chapter an "## Analects <book>.<chapter>" heading numbered by position, which is
Legge's own chapter order, drops the paragraph numbers, and re-flows whitespace (the
download keeps the print's page breaks as blank lines in mid-sentence).

Legge's chapter numbers sometimes differ by one from modern editions: his 15.23 is the
"reciprocity" chapter most modern editions number 15.24. Headings keep Legge's number.

Usage: python scripts/sources/build_confucius.py --root .
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import common

URL = "https://gutenberg.pglaf.org/cache/epub/3330/pg3330.txt"
OUT = "sources/confucius/legge-analects.txt"
EXPECTED_CHAPTERS = (16, 24, 26, 26, 27, 28, 37, 21, 30, 18, 25, 24, 30, 47, 41, 14, 26, 11, 25, 3)
BODY_START = "CONFUCIAN ANALECTS.\nBOOK I."
BODY_END = "*** END OF THE PROJECT GUTENBERG EBOOK"
BOOK_LINE = re.compile(r"^BOOK ([IVXLC]+)\.\s+(.+)$")
CHAPTER_LABEL = re.compile(r"^\s*CHAP(?:TER)?\.?\s+([IVXLC]+)\b\.?\s*")
PARAGRAPH_NUMBER = re.compile(r"^\s*(\d+)\.\s+")
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(roman: str) -> int:
    total = 0
    for index, char in enumerate(roman):
        value = ROMAN_VALUES[char]
        if index + 1 < len(roman) and ROMAN_VALUES[roman[index + 1]] > value:
            total -= value
        else:
            total += value
    return total


def parse(raw: str) -> list[tuple[str, str]]:
    """Return ("Analects B.C", text) for every chapter, in Legge's order."""
    start = raw.index(BODY_START) + len("CONFUCIAN ANALECTS.\n")
    chapters: list[tuple[int, list[list[str]]]] = []  # (book, paragraphs as lists of lines)
    book = 0
    for line in raw[start : raw.index(BODY_END)].split("\n"):
        book_match = BOOK_LINE.match(line)
        if book_match:
            book += 1
            if roman_to_int(book_match.group(1)) != book:
                raise ValueError(f"book out of order: {line!r}")
            continue
        if not line.strip():
            continue
        label = CHAPTER_LABEL.match(line)
        if label:
            line = line[label.end() :]
            number = PARAGRAPH_NUMBER.match(line)
            chapters.append((book, [[line[number.end() :] if number else line]]))
            continue
        if not chapters or chapters[-1][0] != book:
            raise ValueError(f"text before the first chapter label of book {book}: {line!r}")
        number = PARAGRAPH_NUMBER.match(line) if line.startswith(" ") else None
        if number:
            chapters[-1][1].append([line[number.end() :]])
        else:
            chapters[-1][1][-1].append(line)
    per_book = tuple(sum(1 for b, _ in chapters if b == n) for n in range(1, 21))
    if per_book != EXPECTED_CHAPTERS:
        raise ValueError(f"unexpected chapters per book: {per_book}")
    blocks: list[tuple[str, str]] = []
    position = dict.fromkeys(range(1, 21), 0)
    for chapter_book, paragraphs in chapters:
        position[chapter_book] += 1
        text = "\n\n".join(common.normalise(" ".join(lines)) for lines in paragraphs)
        blocks.append((f"Analects {chapter_book}.{position[chapter_book]}", text))
    return blocks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--cache", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    raw = common.decode(common.fetch(URL, Path(args.cache or root / "sources-local" / "cache")))
    blocks = parse(raw)
    common.finish(
        root / OUT,
        raw,
        blocks,
        root,
        {
            "Title": "Confucian Analects (the Lunyu)",
            "Translator": "James Legge (1815-1897)",
            "Published": "1861, in The Chinese Classics, vol. 1; revised 1893",
            "Licence basis": "public domain worldwide (the translator died in 1897)",
            "Downloaded from": f"{URL} (Project Gutenberg ebook 3330, via the pglaf.org mirror)",
            "Retrieved": "2026-11-27",
            "Removed": "the distributor's header, licence and title page; the BOOK lines; the "
            "printed chapter labels and paragraph numbers",
            "Inserted": "one '## Analects B.C' heading per chapter, in Legge's numbering "
            "(his 15.23 is 15.24 in most modern editions)",
            "Structure": f"20 books, {len(blocks)} chapters; chapters per book "
            f"{list(EXPECTED_CHAPTERS)}",
        },
    )


if __name__ == "__main__":
    main()
