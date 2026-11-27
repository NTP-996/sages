#!/usr/bin/env python3
"""Build the Jung sources from two English editions published before 1931.

* Collected Papers on Analytical Psychology, edited by Constance E. Long, second edition
  1917 (Project Gutenberg ebook 48225).
* Psychology of the Unconscious, translated by Beatrice M. Hinkle, 1916 (Project Gutenberg
  ebook 65903).

Both are in the public domain in the United States. Jung died in 1961, so his work is still
in copyright where the term is the author's life plus 70 years, until 2032. This script
therefore writes two things:

* the full texts, to sources-local/jung/ (ignored by git), with one "## <work> <chapter>"
  heading per chapter, for authoring and re-checking passages; and
* with --excerpts, sources/jung/<slug>-excerpts.txt (committed): only the paragraph around
  each passage listed in skills/jung/passages.jsonl, under that chapter's heading.

Usage:
    python scripts/sources/build_jung.py --root .             # full texts, local only
    python scripts/sources/build_jung.py --root . --excerpts  # the committed excerpts
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import common

EDITIONS = {
    "collected-papers": {
        "url": "https://gutenberg.pglaf.org/cache/epub/48225/pg48225.txt",
        "ebook": "48225",
        "label": "Collected Papers",
        "title": "Collected Papers on Analytical Psychology",
        "translator": "edited by Constance E. Long; translated by Constance E. Long, "
        "M. D. Eder and Dora Hecht",
        "published": "1916; second edition 1917",
    },
    "psychology-of-the-unconscious": {
        "url": "https://gutenberg.pglaf.org/cache/epub/65903/pg65903.txt",
        "ebook": "65903",
        "label": "Psychology of the Unconscious",
        "title": "Psychology of the Unconscious: A Study of the Transformations and "
        "Symbolisms of the Libido",
        "translator": "Beatrice M. Hinkle (1874-1953)",
        "published": "1916",
    },
}
CHAPTER = re.compile(r"^\s*CHAPTER ([IVXLC]+)\.?\s*$")
PART = re.compile(r"^\s*PART ([IVXLC]+)\.?\s*$")
MAX_EXCERPT_BYTES = 80_000


def collected_papers(body: str) -> list[tuple[str, str]]:
    """Chapters I to XV. The first run of CHAPTER lines is the table of contents."""
    lines = body.split("\n")
    marks = [(i, m.group(1)) for i, line in enumerate(lines) if (m := CHAPTER.match(line))]
    start = next(k for k in range(1, len(marks)) if marks[k][1] == "I")
    marks = marks[start:]
    blocks: list[tuple[str, str]] = []
    for position, (index, numeral) in enumerate(marks):
        stop = marks[position + 1][0] if position + 1 < len(marks) else len(lines)
        text = "\n".join(lines[index + 1 : stop]).strip("\n")
        blocks.append((f"Collected Papers {numeral}", text))
    return blocks


def psychology_of_the_unconscious(body: str) -> list[tuple[str, str]]:
    """Parts I and II of the main text; the notes that follow repeat the headings and are cut."""
    lines = body.split("\n")
    blocks: list[tuple[str, str]] = []
    part = ""
    seen_parts: list[str] = []
    current: list[str] | None = None
    heading = ""
    for line in lines:
        part_match = PART.match(line)
        chapter_match = CHAPTER.match(line)
        if part_match:
            if blocks and part_match.group(1) == "I" and "II" in seen_parts:
                break  # the notes section starts over at PART I
            part = part_match.group(1)
            seen_parts.append(part)
            continue
        if chapter_match and part:
            if current is not None:
                blocks.append((heading, "\n".join(current).strip("\n")))
            heading = f"Psychology of the Unconscious {part}.{chapter_match.group(1)}"
            if any(existing == heading for existing, _ in blocks):
                current = None  # table of contents repeats; keep the later, longer text
                blocks = [(h, t) for h, t in blocks if h != heading]
            current = []
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        blocks.append((heading, "\n".join(current).strip("\n")))
    return blocks


PARSERS = {
    "collected-papers": collected_papers,
    "psychology-of-the-unconscious": psychology_of_the_unconscious,
}


def build_full(root: Path, cache: Path) -> dict[str, list[tuple[str, str]]]:
    parsed: dict[str, list[tuple[str, str]]] = {}
    for slug, edition in EDITIONS.items():
        raw = common.decode(common.fetch(edition["url"], cache))
        blocks = PARSERS[slug](common.strip_gutenberg(raw))
        out = root / "sources-local" / "jung" / f"{slug}.txt"
        common.write_source(out, blocks)
        common.assert_no_words_changed(raw, out.read_text(encoding="utf-8"))
        print(f"{out.relative_to(root)}: {len(blocks)} chapters, {out.stat().st_size} bytes")
        parsed[slug] = blocks
    return parsed


def build_excerpts(root: Path, parsed: dict[str, list[tuple[str, str]]]) -> None:
    passages = [
        json.loads(line)
        for line in (root / "skills/jung/passages.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    total = 0
    for slug, edition in EDITIONS.items():
        relative = f"sources/jung/{slug}-excerpts.txt"
        wanted = [p for p in passages if p["source_file"] == relative]
        excerpts: list[tuple[str, str]] = []
        for heading, text in parsed[slug]:
            paragraphs = re.split(r"\n\s*\n", text)
            keep = [
                paragraph
                for paragraph in paragraphs
                if any(
                    p["under_heading"] == heading
                    and common.normalise(p["text"]) in common.normalise(paragraph)
                    for p in wanted
                )
            ]
            if keep:
                excerpts.append((heading, "\n\n".join(keep)))
        found = sum(
            1
            for p in wanted
            if any(
                h == p["under_heading"] and common.normalise(p["text"]) in common.normalise(t)
                for h, t in excerpts
            )
        )
        if found != len(wanted):
            raise ValueError(f"{slug}: {len(wanted) - found} passage(s) do not sit in one paragraph")
        out = root / relative
        full = root / "sources-local" / "jung" / f"{slug}.txt"
        common.write_source(out, excerpts)
        total += out.stat().st_size
        common.record_provenance(
            root / "sources" / "PROVENANCE.md",
            relative,
            {
                "Title": f"{edition['title']} (excerpts)",
                "Translator": edition["translator"],
                "Published": edition["published"],
                "Licence basis": "the edition is in the public domain in the United States "
                "(published before 1931). C. G. Jung died in 1961, so the work remains in "
                "copyright where the term is life plus 70 years, until 2032; for that reason "
                "only the paragraphs around the quoted passages are kept here, never the work",
                "Downloaded from": f"{edition['url']} (Project Gutenberg ebook "
                f"{edition['ebook']}, proofread, via the pglaf.org mirror)",
                "Retrieved": "2026-11-27",
                "Removed": "everything except the paragraphs that hold a quoted passage",
                "Inserted": f"one '## {edition['label']} <chapter>' heading per chapter quoted",
                "Structure": f"{len(excerpts)} chapters quoted, {len(wanted)} passages; "
                f"{out.stat().st_size} bytes kept of {full.stat().st_size}",
                "No-words-changed check": "passed",
                "sha256": common.sha256_file(out),
                "bytes": str(out.stat().st_size),
            },
        )
        print(f"{relative}: {len(excerpts)} chapters, {out.stat().st_size} bytes")
    if total > MAX_EXCERPT_BYTES:
        raise ValueError(f"excerpts total {total} bytes, over the {MAX_EXCERPT_BYTES} limit")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--cache", default=None)
    parser.add_argument("--excerpts", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    parsed = build_full(root, Path(args.cache or root / "sources-local" / "cache"))
    if args.excerpts:
        build_excerpts(root, parsed)


if __name__ == "__main__":
    main()
