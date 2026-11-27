#!/usr/bin/env python3
"""Build sources/buddha/sujato-suttas.txt from SuttaCentral.

Bhikkhu Sujato's English translations of the early Buddhist discourses, which SuttaCentral
publishes under Creative Commons Zero (CC0). Each discourse is fetched as translation
segments from the SuttaCentral API; this script writes the segments one per line under a
"## <citation>" heading ("## SN 56.11", "## MN 63"). The Dhammapada gets one heading per
verse ("## Dhp 5"). Title segments (ids ending ":0.n") are dropped.

Usage: python scripts/sources/build_buddha.py --root .
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import common

API = "https://suttacentral.net/api/bilarasuttas/{uid}/sujato?lang=en"
OUT = "sources/buddha/sujato-suttas.txt"
COLLECTION = {"dn": "DN", "mn": "MN", "sn": "SN", "an": "AN", "snp": "Snp", "ud": "Ud", "iti": "Iti"}
DISCOURSES = (
    "dn16 dn31 "
    "mn10 mn19 mn20 mn21 mn22 mn26 mn58 mn61 mn63 mn131 "
    "sn3.25 sn7.2 sn12.2 sn12.15 sn12.61 sn22.1 sn22.59 sn35.28 sn36.6 sn44.10 sn45.2 sn45.8 "
    "sn47.19 sn56.11 sn56.31 "
    "an3.39 an3.65 an3.136 an4.42 an4.62 an5.57 an5.161 an5.198 an6.55 an8.6 an8.54 "
    "snp1.8 snp2.4 snp3.8 "
    "ud1.10 ud6.4 ud8.3 ud8.8"
).split()
DHAMMAPADA = (
    "dhp1-20 dhp21-32 dhp33-43 dhp44-59 dhp60-75 dhp76-89 dhp90-99 dhp100-115 dhp116-128 "
    "dhp129-145 dhp146-156 dhp157-166 dhp167-178 dhp179-196 dhp197-208 dhp209-220 dhp221-234 "
    "dhp235-255 dhp256-272 dhp273-289 dhp290-305 dhp306-319 dhp320-333 dhp334-359 dhp360-382 "
    "dhp383-423"
).split()
UID = re.compile(r"^([a-z]+)(\d+(?:\.\d+)?)$")
TITLE_SEGMENT = re.compile(r":0(\.\d+)?$")
LINE_JOIN = re.compile(r"\s*<j>\s*")
INLINE_MARKUP = re.compile(r"</?(?:em|i|b)>")


def citation(uid: str) -> str:
    match = UID.match(uid)
    if match is None or match.group(1) not in COLLECTION:
        raise ValueError(f"cannot turn {uid!r} into a citation")
    return f"{COLLECTION[match.group(1)]} {match.group(2)}"


def segments(payload: bytes) -> list[tuple[str, str]]:
    """Return (segment id, translation text) in reading order, without title segments."""
    data = json.loads(payload)
    text = data["translation_text"]
    return [
        (key, INLINE_MARKUP.sub("", LINE_JOIN.sub("\n", text[key])).strip())
        for key in data["keys_order"]
        if key in text and text[key].strip() and not TITLE_SEGMENT.search(key)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--cache", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    cache = Path(args.cache or root / "sources-local" / "cache")

    blocks: list[tuple[str, str]] = []
    raw_lines: list[str] = []
    for uid in DISCOURSES:
        found = segments(common.fetch(API.format(uid=uid), cache))
        raw_lines.extend(text for _, text in found)
        blocks.append((citation(uid), "\n".join(text for _, text in found)))
    verses: dict[int, list[str]] = {}
    for uid in DHAMMAPADA:
        for key, text in segments(common.fetch(API.format(uid=uid), cache)):
            raw_lines.append(text)
            verses.setdefault(int(key.split(":")[0].removeprefix("dhp")), []).append(text)
    if sorted(verses) != list(range(1, 424)):
        raise ValueError(f"expected Dhammapada verses 1-423, found {len(verses)}")
    blocks.extend((f"Dhp {number}", "\n".join(verses[number])) for number in sorted(verses))

    common.finish(
        root / OUT,
        "\n".join(raw_lines),
        blocks,
        root,
        {
            "Title": "Discourses of the Buddha from the Pali Canon: a selection from the Long, "
            "Middle, Linked and Numbered Discourses, the Udana and the Sutta Nipata, and the "
            "whole Dhammapada",
            "Translator": "Bhikkhu Sujato",
            "Published": "2018, SuttaCentral",
            "Licence basis": "Creative Commons Zero (CC0), https://creativecommons.org/publicdomain/zero/1.0/ "
            "- SuttaCentral's publication record states: 'It is dedicated to the public domain "
            "via Creative Commons Zero (CC0).'",
            "Downloaded from": API.format(uid="<uid>") + " for each uid listed in "
            "scripts/sources/build_buddha.py",
            "Retrieved": "2026-11-27",
            "Removed": "the Pali root text, variant readings and references; title segments; the "
            "<em> emphasis tags; the <j> verse line-join marks (replaced by a line break)",
            "Inserted": "one heading per discourse ('## SN 56.11') and per Dhammapada verse "
            "('## Dhp 5'); one translation segment per line",
            "Structure": f"{len(DISCOURSES)} discourses and 423 Dhammapada verses",
        },
    )


if __name__ == "__main__":
    main()
