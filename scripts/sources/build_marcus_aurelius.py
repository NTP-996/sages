#!/usr/bin/env python3
"""Build sources/marcus-aurelius/long-meditations.txt from Project Gutenberg ebook 15877.

George Long's translation, "The Thoughts of the Emperor Marcus Aurelius Antoninus" (1862).
The download prints each book under a Roman numeral, leaves the first section of a book
unnumbered and numbers the rest ("2. ...", "3. ..."), and carries Long's footnotes as
indented blocks keyed by "[A]", "[B]" marks in the text. This script keeps the twelve books
of the Thoughts only, drops the footnote blocks and their marks, and gives every section a
"## Meditations <book>.<section>" heading in Long's own numbering. Long's bracketed
insertions ("[only]", "[the same]") and his "+" marks on doubtful text are part of the
translation and are kept.

Usage: python scripts/sources/build_marcus_aurelius.py --root .
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import common

URL = "https://gutenberg.pglaf.org/cache/epub/15877/pg15877.txt"
OUT = "sources/marcus-aurelius/long-meditations.txt"
ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")
BOOK_LINE = re.compile(r"^\s*([IVX]+)\.\s*$")
FOOTNOTE_MARK = re.compile(r"\[[A-Z]\]")
FOOTNOTE_BLOCK = re.compile(r"^\s+\[[A-Z]\]\s")
SECTION_NUMBER = re.compile(r"^(\d+)\.\s+")


def without_footnote_marks(text: str) -> str:
    return FOOTNOTE_MARK.sub("", text)


def parse(raw: str) -> tuple[list[tuple[str, str]], list[int]]:
    """Return the ("Meditations B.S", text) blocks and the number of sections per book."""
    lines = common.strip_gutenberg(raw).split("\n")
    marks = [i for i, line in enumerate(lines) if BOOK_LINE.match(line)]
    if [BOOK_LINE.match(lines[i]).group(1) for i in marks] != list(ROMAN):  # type: ignore[union-attr]
        raise ValueError("the twelve book markers I. to XII. were not found in order")
    end = next(i for i, line in enumerate(lines) if i > marks[-1] and line.strip() == "INDEXES.")
    blocks: list[tuple[str, str]] = []
    per_book: list[int] = []
    for book, start in enumerate(marks, start=1):
        stop = marks[book] if book < len(marks) else end
        paragraphs = [p for p in re.split(r"\n\s*\n", "\n".join(lines[start + 1 : stop])) if p.strip()]
        sections: list[list[str]] = []
        in_footnote = False
        for paragraph in paragraphs:
            indented = paragraph.startswith((" ", "\t"))
            if FOOTNOTE_BLOCK.match(paragraph) or (in_footnote and indented):
                in_footnote = True
                continue
            in_footnote = False
            text = without_footnote_marks(paragraph).strip("\n")
            number = SECTION_NUMBER.match(text)
            if number and int(number.group(1)) == len(sections) + 1 and sections:
                sections.append([text[number.end() :]])
            elif not sections:
                sections.append([text])
            else:
                sections[-1].append(text)
        per_book.append(len(sections))
        blocks.extend(
            (f"Meditations {book}.{index}", "\n\n".join(parts))
            for index, parts in enumerate(sections, start=1)
        )
    return blocks, per_book


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--cache", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    raw = common.decode(common.fetch(URL, Path(args.cache or root / "sources-local" / "cache")))
    blocks, per_book = parse(raw)
    common.finish(
        root / OUT,
        without_footnote_marks(raw),
        blocks,
        root,
        {
            "Title": "The Thoughts of the Emperor Marcus Aurelius Antoninus (the Meditations)",
            "Translator": "George Long (1800-1879)",
            "Published": "1862",
            "Licence basis": "public domain worldwide (the translator died in 1879)",
            "Downloaded from": f"{URL} (Project Gutenberg ebook 15877, via the pglaf.org mirror)",
            "Retrieved": "2026-11-27",
            "Removed": "the distributor's header and licence; Long's biographical sketch and "
            "essay on the philosophy of Antoninus; the indexes; footnote blocks and their "
            "[A]-style marks; each section's printed number",
            "Inserted": "one '## Meditations B.S' heading per section, in Long's numbering",
            "Structure": f"12 books, {sum(per_book)} sections; sections per book {per_book}",
        },
    )


if __name__ == "__main__":
    main()
