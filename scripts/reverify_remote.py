#!/usr/bin/env python3
"""Re-check the passages whose source text is not kept in this repository.

* Remote-policy passages (Charlie Munger): fetch each passage's source_url and check that
  its text is on the page, word for word.
* Carl Jung: rebuild the two full editions locally (they are not committed; see
  sources/PROVENANCE.md) and check each passage against the chapter it names.

Usage:
    python scripts/reverify_remote.py --root . [--sage munger|jung]

This needs the network, so it is not part of CI. Paste its dated report into
sources/PROVENANCE.md when you run it. Dev tooling only. Standard library only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "sources"))

import common

SKIPPED_TAGS = {"script", "style", "noscript", "template"}
Record = dict[str, object]


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skipping: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIPPED_TAGS:
            self._skipping.append(tag)
        else:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self._skipping and self._skipping[-1] == tag:
            self._skipping.pop()
        else:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skipping:
            self.parts.append(data)


def visible_text(html: str) -> str:
    """The text a reader sees on the page, whitespace-normalised."""
    parser = _VisibleText()
    parser.feed(html)
    parser.close()
    text = common.normalise("".join(parser.parts))
    # Inline tags leave a space before punctuation ("deserve </b>what"): close those gaps.
    for mark in ".,;:!?":
        text = text.replace(f" {mark}", mark)
    return text


def _records(root: Path, sage: str | None) -> list[Record]:
    found: list[Record] = []
    for path in sorted((root / "skills").glob("*/passages.jsonl")):
        if sage is not None and path.parent.name != sage:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                found.append(json.loads(line))
    return found


def check_remote(
    root: Path, fetch: Callable[[str], str], sage: str | None = None
) -> tuple[int, list[str]]:
    """Check every passage that carries a source_url. Returns (passages checked, problems)."""
    pages: dict[str, str | None] = {}
    problems: list[str] = []
    checked = 0
    for record in _records(root, sage):
        url = record.get("source_url")
        if not isinstance(url, str):
            continue
        checked += 1
        if url not in pages:
            try:
                pages[url] = visible_text(fetch(url))
            except (OSError, ValueError) as error:
                pages[url] = None
                problems.append(f"{record.get('id')}: could not fetch {url} ({error})")
                continue
        page = pages[url]
        if page is None:
            problems.append(f"{record.get('id')}: could not fetch {url}")
        elif common.normalise(str(record.get("text", ""))) not in page:
            problems.append(f"{record.get('id')}: text not found on {url}")
    return checked, problems


def check_jung(root: Path, cache: Path) -> tuple[int, list[str]]:
    """Check each Jung passage against the full edition, under the chapter it names."""
    import build_jung

    parsed = build_jung.build_full(root, cache)
    chapters = {
        f"sources/jung/{slug}-excerpts.txt": {
            heading: common.normalise(text) for heading, text in blocks
        }
        for slug, blocks in parsed.items()
    }
    problems: list[str] = []
    records = _records(root, "jung")
    for record in records:
        chapter = chapters.get(str(record.get("source_file")), {}).get(
            str(record.get("under_heading"))
        )
        if chapter is None or common.normalise(str(record.get("text", ""))) not in chapter:
            problems.append(f"{record.get('id')}: not found in the full edition")
    return len(records), problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--sage", choices=("munger", "jung"), default=None)
    parser.add_argument("--cache", default=None, help="download cache (default: a fresh fetch)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    cache = Path(args.cache or root / "sources-local" / "reverify-cache")

    def fetch(url: str) -> str:
        return common.fetch(url, cache).decode("utf-8", errors="replace")

    today = datetime.date.today().isoformat()
    problems: list[str] = []
    if args.sage in (None, "munger"):
        checked, found = check_remote(root, fetch, "munger")
        print(
            f"{today}: {checked - len(found)}/{checked} remote passages found at their source_url"
        )
        problems += found
    if args.sage in (None, "jung"):
        checked, found = check_jung(root, cache)
        print(f"{today}: {checked - len(found)}/{checked} Jung passages found in the full editions")
        problems += found
    for problem in problems:
        print(f"- {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
