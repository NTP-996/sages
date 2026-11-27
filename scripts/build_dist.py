#!/usr/bin/env python3
"""Build the release artefacts that are not a plain clone of the repository.

Usage:
    python scripts/build_dist.py --root . --zips dist/skills --hermes dist/hermes

* --zips: one ZIP per skill, holding <skill>/SKILL.md and the data file beside it. Claude and
  ChatGPT take a skill as an uploaded ZIP; a teacher's ZIP works on its own.
* --hermes: the files Hermes Agent needs and no others (the manifest, the adapter, the skills
  without their scenario suites). Hermes scans a plugin's whole tree at install and blocks
  repositories that carry dev tooling, so the release publishes this tree on the "hermes" branch.

Dev tooling only. Standard library only.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

SKILL_FILES = ("SKILL.md", "passages.jsonl", "roster.json")
HERMES_FILES = (
    "plugin.yaml",
    "__init__.py",
    "after-install.md",
    "INSTALL_FOR_HERMES.md",
    "LICENSE",
    "NOTICE",
)
HERMES_README = """# Sages for Hermes Agent

This branch is the Hermes Agent build of https://github.com/NTP-996/sages: the plugin manifest,
the adapter and the nine skills, and nothing else. It is generated from the main branch at each
release; do not edit it by hand. See INSTALL_FOR_HERMES.md.
"""
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def _skills(root: Path) -> list[Path]:
    return sorted(p for p in (root / "skills").iterdir() if (p / "SKILL.md").is_file())


def build_skill_zips(root: Path, out_dir: Path) -> list[Path]:
    """Write <out_dir>/<skill>.zip for every skill. Byte-identical for identical input."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for skill in _skills(root):
        target = out_dir / f"{skill.name}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in SKILL_FILES:
                source = skill / name
                if source.is_file():
                    info = zipfile.ZipInfo(f"{skill.name}/{name}", date_time=FIXED_TIME)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    archive.writestr(info, source.read_bytes())
        written.append(target)
    return written


def build_hermes_tree(root: Path, out_dir: Path) -> Path:
    """Write the Hermes Agent build into out_dir, replacing whatever was there."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    for name in HERMES_FILES:
        shutil.copy2(root / name, out_dir / name)
    (out_dir / "README.md").write_text(HERMES_README, encoding="utf-8")
    for skill in _skills(root):
        target = out_dir / "skills" / skill.name
        target.mkdir(parents=True)
        for name in SKILL_FILES:
            if (skill / name).is_file():
                shutil.copy2(skill / name, target / name)
    return out_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--zips", help="directory for the per-skill ZIP files")
    parser.add_argument("--hermes", help="directory for the Hermes Agent build")
    args = parser.parse_args(argv)
    if not (args.zips or args.hermes):
        parser.error("choose --zips and/or --hermes")
    root = Path(args.root).resolve()
    if args.zips:
        print(f"wrote {len(build_skill_zips(root, Path(args.zips)))} skill ZIP(s) to {args.zips}")
    if args.hermes:
        print(f"wrote the Hermes Agent build to {build_hermes_tree(root, Path(args.hermes))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
