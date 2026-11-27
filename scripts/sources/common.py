"""Helpers shared by the source build scripts.

A build script downloads one edition, strips what is not the translator's text, inserts one
"## <citation>" heading per chapter, section, discourse or verse, and proves that it changed
no word of the text. Dev tooling only. Standard library only.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
import urllib.request
from pathlib import Path

USER_AGENT = "sages-source-builder/0.1 (+https://github.com/NTP-996/sages)"
GUTENBERG_START = re.compile(r"^\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*$", re.MULTILINE)
GUTENBERG_END = re.compile(r"^\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*$", re.MULTILINE)
WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """NFC, with each whitespace run collapsed to one space."""
    return WHITESPACE.sub(" ", unicodedata.normalize("NFC", text)).strip()


def cache_path(url: str, cache_dir: Path) -> Path:
    """Where the bytes downloaded from url are kept."""
    return cache_dir / hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


def fetch(url: str, cache_dir: Path) -> bytes:
    """Return the bytes at url, downloading once and reading the cache afterwards."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_path(url, cache_dir)
    if cached.is_file():
        return cached.read_bytes()
    if not url.startswith("https://"):
        raise ValueError(f"refusing to fetch a non-https URL: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - https only
        data: bytes = response.read()
    cached.write_bytes(data)
    return data


def decode(data: bytes) -> str:
    """Decode a download as UTF-8 (dropping a byte-order mark) with Unix line endings."""
    return data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def strip_gutenberg(text: str) -> str:
    """Return only the body between Project Gutenberg's START and END markers."""
    start = GUTENBERG_START.search(text)
    end = GUTENBERG_END.search(text)
    if start is None or end is None:
        raise ValueError("Project Gutenberg START/END markers not found")
    return text[start.end() : end.start()].strip()


def assert_no_words_changed(raw: str, cleaned: str) -> None:
    """Raise ValueError unless every non-heading paragraph of cleaned is verbatim in raw."""
    haystack = normalise(raw)
    for paragraph in re.split(r"\n\s*\n", cleaned):
        lines = [line for line in paragraph.splitlines() if not line.startswith("## ")]
        needle = normalise("\n".join(lines))
        if needle and needle not in haystack:
            raise ValueError(f"paragraph not found verbatim in the download: {needle[:120]!r}")


def write_source(path: Path, blocks: list[tuple[str, str]]) -> None:
    """Write (heading, text) blocks as a source file. Headings must be unique."""
    seen: set[str] = set()
    parts: list[str] = []
    for heading, body in blocks:
        if heading in seen:
            raise ValueError(f"duplicate heading {heading!r}")
        seen.add(heading)
        parts.append(f"## {heading}\n\n{body.strip()}\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_provenance(provenance: Path, relative: str, fields: dict[str, str]) -> None:
    """Write or replace the "## <relative>" section of PROVENANCE.md, leaving the rest alone."""
    section = f"## {relative}\n\n" + "".join(f"- {key}: {value}\n" for key, value in fields.items())
    text = provenance.read_text(encoding="utf-8") if provenance.is_file() else "# Provenance\n"
    pattern = re.compile(rf"^## {re.escape(relative)}\n.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    if pattern.search(text):
        text = pattern.sub(lambda _: section + "\n", text)
    else:
        text = text.rstrip("\n") + "\n\n" + section
    provenance.write_text(text.rstrip("\n") + "\n", encoding="utf-8")


def finish(
    out_file: Path, raw: str, blocks: list[tuple[str, str]], root: Path, fields: dict[str, str]
) -> None:
    """Write the source file, prove no word changed, and record its provenance."""
    write_source(out_file, blocks)
    assert_no_words_changed(raw, out_file.read_text(encoding="utf-8"))
    relative = out_file.resolve().relative_to(root.resolve()).as_posix()
    record_provenance(
        root / "sources" / "PROVENANCE.md",
        relative,
        {
            **fields,
            "No-words-changed check": "passed",
            "sha256": sha256_file(out_file),
            "bytes": str(out_file.stat().st_size),
        },
    )
    print(f"{relative}: {len(blocks)} headings, {out_file.stat().st_size} bytes")
