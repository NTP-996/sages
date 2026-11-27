#!/usr/bin/env python3
"""Build sources/laozi/legge-tao-teh-king.txt from Project Gutenberg ebook 216.

James Legge's translation of the Tao Teh King (Sacred Books of the East, vol. 39, 1891).
The download separates chapters with two blank lines and opens each with its number
("Ch. 1. 1. ...", "2. 1. ...", "6." on a line of its own, "11. The thirty spokes ...").
This script replaces that chapter number with a "## Chapter N" heading and keeps
everything else, including Legge's own verse numbers and his bracketed insertions.

Usage: python scripts/sources/build_laozi.py --root .
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import common

URL = "https://gutenberg.pglaf.org/cache/epub/216/pg216.txt"
OUT = "sources/laozi/legge-tao-teh-king.txt"
CHAPTERS = 81
CHAPTER_OPENING = re.compile(r"^(?:Ch\. )?(\d+)\.[ \t]*\n?")
VERSE_NUMBER = re.compile(r"^(\d+)\.(?:\s|$)")


def parse(raw: str) -> list[tuple[str, str]]:
    """Return ("Chapter N", text) for the 81 chapters, in order."""
    body = common.strip_gutenberg(raw)
    blocks: list[tuple[str, str]] = []
    for chunk in re.split(r"\n[ \t]*\n[ \t]*\n+", body):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        opening = CHAPTER_OPENING.match(chunk)
        if opening and int(opening.group(1)) == len(blocks) + 1:
            blocks.append((f"Chapter {len(blocks) + 1}", chunk[opening.end() :].strip("\n")))
        elif blocks and not chunk.strip().startswith("PART"):
            heading, text = blocks[-1]
            blocks[-1] = (heading, f"{text}\n\n{chunk}")
    if len(blocks) != CHAPTERS:
        raise ValueError(f"expected {CHAPTERS} chapters, found {len(blocks)}")
    for heading, text in blocks:
        numbers = [
            int(match.group(1))
            for paragraph in re.split(r"\n\s*\n", text)
            if (match := VERSE_NUMBER.match(paragraph.strip()))
        ]
        if numbers and numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"{heading}: verse numbers are {numbers}, so a chapter was mis-split")
    return [(heading, "\n".join(line.rstrip() for line in text.splitlines())) for heading, text in blocks]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--cache", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    raw = common.decode(common.fetch(URL, Path(args.cache or root / "sources-local" / "cache")))
    common.finish(
        root / OUT,
        raw,
        parse(raw),
        root,
        {
            "Title": "The Tao Teh King, or The Tao and Its Characteristics",
            "Translator": "James Legge (1815-1897)",
            "Published": "1891, in The Sacred Books of the East, vol. 39",
            "Licence basis": "public domain worldwide (the translator died in 1897)",
            "Downloaded from": f"{URL} (Project Gutenberg ebook 216, via the pglaf.org mirror)",
            "Retrieved": "2026-11-27",
            "Removed": "the distributor's header, licence and title page; the PART markers; "
            "each chapter's printed number",
            "Inserted": "one '## Chapter N' heading per chapter",
            "Structure": f"{CHAPTERS} chapters; Legge's verse numbers are kept",
        },
    )


if __name__ == "__main__":
    main()
