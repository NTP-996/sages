#!/usr/bin/env python3
"""Check that every passage in skills/*/passages.jsonl is what its source says.

Usage:
    python scripts/verify_passages.py --root .

Two source policies:

* local  - the passage names a file under sources/ and the heading it sits under. Its text,
           with every run of whitespace collapsed to one space, must be a contiguous substring
           of that file normalised the same way, and the nearest preceding "## " heading must
           be the one named. Nothing else is normalised: case, punctuation and quote
           characters must match the source exactly.
* remote - the passage carries a source title, an https URL and the date it was checked, and
           no source text is kept in the repository. scripts/reverify_remote.py re-checks
           these against the live source.

Dev tooling only: nothing here ships to a harness. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Literal

SOURCE_POLICY: dict[str, Literal["local", "remote"]] = {
    "buddha": "local",
    "laozi": "local",
    "confucius": "local",
    "marcus-aurelius": "local",
    "epictetus": "local",
    "jung": "local",
    "munger": "remote",
}

COMMON_FIELDS = ("id", "sage", "text", "citation", "work", "year", "themes")
LOCAL_FIELDS = ("translator", "source_file", "under_heading")
REMOTE_FIELDS = ("source_title", "source_url", "checked")

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WHITESPACE = re.compile(r"\s+")
MIN_TEXT_CHARS = 20
MAX_LOCAL_TEXT_CHARS = 600
MAX_REMOTE_TEXT_CHARS = 300

Record = dict[str, object]


def normalise(text: str) -> str:
    """Return text in NFC form with each whitespace run collapsed to a single space."""
    return WHITESPACE.sub(" ", unicodedata.normalize("NFC", text)).strip()


def load_passages(path: Path) -> list[Record]:
    """Read one passages.jsonl. Raises ValueError naming the line that is not valid JSON."""
    records: list[Record] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except ValueError as error:
            raise ValueError(f"line {line_number} is not valid JSON ({error})") from error
        if not isinstance(parsed, dict):
            raise ValueError(f"line {line_number} is not valid JSON (expected an object)")
        records.append(parsed)
    return records


class _Source:
    """One source file, normalised once, with a line number for every normalised character."""

    def __init__(self, path: Path) -> None:
        text = unicodedata.normalize("NFC", path.read_text(encoding="utf-8"))
        self.lines = text.splitlines()
        chars: list[str] = []
        line_of: list[int] = []
        line = 1
        pending_space = False
        for char in text:
            if char.isspace():
                if char == "\n":
                    line += 1
                pending_space = bool(chars)
                continue
            if pending_space:
                chars.append(" ")
                line_of.append(line)
                pending_space = False
            chars.append(char)
            line_of.append(line)
        self.normalised = "".join(chars)
        self._line_of = line_of

    def find_all(self, text: str) -> list[int]:
        """Return the 1-based line of every place text starts; empty when it is not in the file."""
        needle = normalise(text)
        lines: list[int] = []
        offset = self.normalised.find(needle)
        while offset >= 0:
            lines.append(self._line_of[offset])
            offset = self.normalised.find(needle, offset + 1)
        return lines

    def heading_before(self, line_number: int) -> str | None:
        for index in range(min(line_number, len(self.lines)) - 1, -1, -1):
            if self.lines[index].startswith("## "):
                return self.lines[index][3:].strip()
        return None


def _shape_problems(record: Record, folder: str, seen_ids: set[str]) -> list[str]:
    problems = [f"missing field '{name}'" for name in COMMON_FIELDS if name not in record]
    if problems:
        return problems
    passage_id, sage, text = record["id"], record["sage"], record["text"]
    if sage != folder:
        problems.append(f"sage {sage!r} does not match the skill folder {folder!r}")
    if not isinstance(passage_id, str) or not KEBAB.match(passage_id):
        problems.append(f"id {passage_id!r} is not lower-kebab-case")
    else:
        if not passage_id.startswith(f"{folder}-"):
            problems.append(f"id {passage_id!r} must start with '{folder}-'")
        if passage_id in seen_ids:
            problems.append(f"duplicate id {passage_id!r}")
    if not isinstance(text, str) or len(normalise(text)) < MIN_TEXT_CHARS:
        problems.append(f"text must be a string of at least {MIN_TEXT_CHARS} characters")
    if not isinstance(record["year"], int) or isinstance(record["year"], bool):
        problems.append("year is not an integer")
    for name in ("citation", "work"):
        if not isinstance(record[name], str) or not str(record[name]).strip():
            problems.append(f"{name} is empty")
    themes = record["themes"]
    if (
        not isinstance(themes, list)
        or not themes
        or not all(isinstance(theme, str) and KEBAB.match(theme) for theme in themes)
    ):
        problems.append("themes must be a non-empty list of lower-kebab-case strings")
    return problems


def _local_problems(record: Record, root: Path, cache: dict[Path, _Source]) -> list[str]:
    problems = [f"missing field '{name}'" for name in LOCAL_FIELDS if name not in record]
    if problems:
        return problems
    text = str(record["text"])
    if len(normalise(text)) > MAX_LOCAL_TEXT_CHARS:
        problems.append(f"text is longer than {MAX_LOCAL_TEXT_CHARS} characters")
    sources_dir = (root / "sources").resolve()
    source_path = (root / str(record["source_file"])).resolve()
    if sources_dir not in source_path.parents or not source_path.is_file():
        return [*problems, f"source_file {record['source_file']!r} is not a file under sources/"]
    if source_path not in cache:
        cache[source_path] = _Source(source_path)
    source = cache[source_path]
    lines = source.find_all(text)
    if not lines:
        return [*problems, f"text not found verbatim in {record['source_file']}"]
    # A line can recur (a refrain, a formula): it verifies if any occurrence sits under the
    # heading the passage names.
    headings = [source.heading_before(line) for line in lines]
    if record["under_heading"] not in headings:
        problems.append(
            f"found at line {lines[0]} under heading {headings[0]!r}, "
            f"but under_heading says {record['under_heading']!r}"
        )
    return problems


def _remote_problems(record: Record) -> list[str]:
    problems = [f"missing field '{name}'" for name in REMOTE_FIELDS if name not in record]
    if "source_file" in record:
        problems.append("a remote-policy passage must not carry source_file")
    if len(normalise(str(record["text"]))) > MAX_REMOTE_TEXT_CHARS:
        problems.append(f"text is longer than {MAX_REMOTE_TEXT_CHARS} characters")
    if problems:
        return problems
    if not str(record["source_url"]).startswith("https://"):
        problems.append("source_url must start with https://")
    if not str(record["source_title"]).strip():
        problems.append("source_title is empty")
    if not ISO_DATE.match(str(record["checked"])):
        problems.append("checked must be a date written YYYY-MM-DD")
    return problems


def verify(root: Path) -> tuple[int, list[str]]:
    """Check every passage under root. Returns (passages seen, problems found)."""
    root = root.resolve()
    cache: dict[Path, _Source] = {}
    seen_ids: set[str] = set()
    problems: list[str] = []
    total = 0
    for passages_path in sorted((root / "skills").glob("*/passages.jsonl")):
        folder = passages_path.parent.name
        where = f"skills/{folder}/passages.jsonl"
        try:
            records = load_passages(passages_path)
        except ValueError as error:
            problems.append(f"{where}: {error}")
            continue
        for record in records:
            total += 1
            label = f"{where}: {record.get('id', '<no id>')}"
            found = _shape_problems(record, folder, seen_ids)
            if isinstance(record.get("id"), str):
                seen_ids.add(str(record["id"]))
            if not found:
                policy = SOURCE_POLICY.get(folder)
                if policy is None:
                    found = [f"no source policy for sage {folder!r}"]
                elif policy == "local":
                    found = _local_problems(record, root, cache)
                else:
                    found = _remote_problems(record)
            problems.extend(f"{label}: {problem}" for problem in found)
    return total, problems


def count_by_policy(root: Path) -> tuple[int, int]:
    """Return (passages compared with a committed source, remote passages checked for form)."""
    local = remote = 0
    for passages_path in sorted((root.resolve() / "skills").glob("*/passages.jsonl")):
        try:
            count = len(load_passages(passages_path))
        except ValueError:
            continue
        if SOURCE_POLICY.get(passages_path.parent.name) == "remote":
            remote += count
        else:
            local += count
    return local, remote


def check_passages(root: Path) -> list[str]:
    """Return one line per problem; an empty list means every passage is what its source says."""
    return verify(root)[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    args = parser.parse_args(argv)
    total, problems = verify(Path(args.root))
    if total == 0 and not problems:
        print("Passage check failed: no passages found under skills/*/passages.jsonl")
        return 1
    if problems:
        print(f"Passage check failed ({len(problems)} problem(s) in {total} passage(s)):")
        for problem in problems:
            print(f"- {problem}")
        return 1
    local, remote = count_by_policy(Path(args.root))
    one = local == 1
    print(
        f"{local} passage{'' if one else 's'} verified against "
        f"{'its committed source' if one else 'their committed sources'}"
    )
    if remote:
        print(
            f"{remote} remote passage{'' if remote == 1 else 's'} checked for form only "
            "(scripts/reverify_remote.py compares them with their live sources)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
