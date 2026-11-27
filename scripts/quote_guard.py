#!/usr/bin/env python3
"""Refuse any quotation in a skill that is not one of that skill's verified passages.

Usage:
    python scripts/quote_guard.py --root .

Two rules, applied to every skills/*/SKILL.md:

1. Under "## Passages", each list item is written
       - "<text>" — <citation>
   and must be the text and the citation of a record in passages.jsonl beside the skill.
2. Anywhere else in the file, a span inside double quotation marks (straight or curly) of
   more than MAX_FREE_QUOTE_WORDS words must be the text of such a record. Short quoted
   phrases, such as something a user might type, are left alone.

scripts/verify_passages.py checks the records against their sources; this script makes sure
nothing reaches a skill except those records. Dev tooling only. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from verify_passages import normalise

MAX_FREE_QUOTE_WORDS = 7
PASSAGE_ITEM = re.compile(r'^- "(?P<text>.+)" — (?P<citation>.+)$')
QUOTED = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')
HEADING = re.compile(r"^## (.+)$")


def _records(skill_dir: Path) -> dict[str, str]:
    """Map each passage's normalised text to its citation."""
    path = skill_dir / "passages.jsonl"
    if not path.is_file():
        return {}
    found: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            found[normalise(str(record["text"]))] = str(record["citation"])
    return found


def _skill_problems(skill_md: Path) -> list[str]:
    records = _records(skill_md.parent)
    problems: list[str] = []
    section = ""
    for number, line in enumerate(skill_md.read_text(encoding="utf-8").splitlines(), start=1):
        heading = HEADING.match(line)
        if heading:
            section = heading.group(1).strip()
            continue
        where = f"{skill_md.parent.name}/SKILL.md:{number}"
        if section == "Passages" and line.startswith("- "):
            item = PASSAGE_ITEM.match(line)
            if item is None:
                problems.append(f'{where}: a passage must be written - "<text>" — <citation>')
                continue
            citation = records.get(normalise(item.group("text")))
            if citation is None:
                problems.append(f"{where}: not a verified passage: {item.group('text')[:60]!r}")
            elif citation != item.group("citation").strip():
                problems.append(
                    f"{where}: cited as {item.group('citation').strip()!r}, "
                    f"but the record says {citation!r}"
                )
            continue
        for match in QUOTED.finditer(line):
            span = match.group(1) or match.group(2)
            if len(span.split()) > MAX_FREE_QUOTE_WORDS and normalise(span) not in records:
                problems.append(f"{where}: unverified quotation: {span[:60]!r}")
    return problems


def find_problems(root: Path) -> list[str]:
    """Return one line per unverified quotation; empty when every skill is clean."""
    problems: list[str] = []
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        problems.extend(_skill_problems(skill_md))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    problems = find_problems(root)
    if problems:
        print(f"Quote guard failed ({len(problems)} problem(s)):")
        for problem in problems:
            print(f"- {problem}")
        return 1
    count = len(list((root / "skills").glob("*/SKILL.md")))
    print(f"Quote guard: {count} skill file(s) clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
