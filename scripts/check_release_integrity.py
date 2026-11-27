#!/usr/bin/env python3
"""Check that every manifest carries the same version, and that releases bump it.

Usage:
    python scripts/check_release_integrity.py --root . --check-version-sync
    python scripts/check_release_integrity.py --root . --check-version-bump --base <git rev>

Each harness reads its own manifest, so a release that forgets one of them ships an update
that some users never receive. The bump check fails a change that touches what users install
(skills/ or src/) without raising the version. Dev tooling only. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PRIMARY_MANIFEST = Path(".claude-plugin/plugin.json")
VERSION_MANIFESTS = (
    Path("plugin.json"),
    PRIMARY_MANIFEST,
    Path(".codex-plugin/plugin.json"),
    Path(".cursor-plugin/plugin.json"),
    Path(".factory-plugin/plugin.json"),
    Path("gemini-extension.json"),
    Path("package.json"),
    Path("plugin.yaml"),
    Path("pyproject.toml"),
    Path("server.json"),
)
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
YAML_VERSION = re.compile(r"""^version:[ \t]*["']?([^"'\s#]+)["']?[ \t]*$""", re.MULTILINE)
SHIPPED_PREFIXES = ("skills/", "src/")


def _versions_in(path: Path) -> list[str]:
    """Return every version a manifest states. Raises OSError or ValueError when unreadable."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        match = YAML_VERSION.search(text)
        return [match.group(1)] if match else []
    if path.suffix == ".toml":
        return [str(tomllib.loads(text).get("project", {}).get("version", ""))]
    data = json.loads(text)
    versions = [str(data.get("version", ""))]
    # The MCP registry entry repeats the version for each package it lists.
    versions += [str(package.get("version", "")) for package in data.get("packages", [])]
    return versions


def _read(root: Path) -> tuple[dict[Path, list[str]], list[str]]:
    found: dict[Path, list[str]] = {}
    problems: list[str] = []
    for relative in VERSION_MANIFESTS:
        try:
            versions = _versions_in(root / relative)
        except (OSError, ValueError) as error:
            problems.append(f"{relative.as_posix()}: cannot read a version ({error})")
            continue
        if not versions or not all(versions):
            problems.append(f"{relative.as_posix()}: no version found")
            continue
        bad = [version for version in versions if not SEMVER.match(version)]
        if bad:
            problems.append(f"{relative.as_posix()}: version {bad[0]!r} is not semver x.y.z")
            continue
        found[relative] = versions
    return found, problems


def check_version_sync(root: Path) -> list[str]:
    """Return one line per manifest that is missing, unreadable or out of step."""
    found, problems = _read(root)
    primary = found.get(PRIMARY_MANIFEST)
    if primary is None:
        return problems or [f"{PRIMARY_MANIFEST.as_posix()}: the primary manifest has no version"]
    expected = primary[0]
    for relative, versions in found.items():
        for version in versions:
            if version != expected:
                problems.append(
                    f"{relative.as_posix()}: version {version} does not match {expected} "
                    f"in {PRIMARY_MANIFEST.as_posix()}"
                )
    return problems


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _is_shipped(path: str) -> bool:
    parts = path.split("/")
    is_scenario_suite = len(parts) >= 4 and parts[0] == "skills" and parts[2] == "evals"
    return path.startswith(SHIPPED_PREFIXES) and not is_scenario_suite


def check_version_bump(root: Path, base: str) -> list[str]:
    """Fail when shipped files changed since base without a higher version."""
    try:
        changed = [p for p in _git(root, "diff", "--name-only", f"{base}...HEAD").splitlines() if p]
        before = json.loads(_git(root, "show", f"{base}:{PRIMARY_MANIFEST.as_posix()}"))["version"]
    except (RuntimeError, ValueError, KeyError) as error:
        return [f"cannot compare with {base}: {error}"]
    shipped = [path for path in changed if _is_shipped(path)]
    if not shipped:
        return []
    now = json.loads((root / PRIMARY_MANIFEST).read_text(encoding="utf-8"))["version"]
    if tuple(map(int, now.split("."))) > tuple(map(int, str(before).split("."))):
        return []
    return [
        f"shipped files changed without a version bump ({before} -> {now}): "
        + ", ".join(shipped[:8])
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--check-version-sync", action="store_true")
    parser.add_argument("--check-version-bump", action="store_true")
    parser.add_argument("--base", help="git revision to compare with for --check-version-bump")
    args = parser.parse_args(argv)
    if not (args.check_version_sync or args.check_version_bump):
        parser.error("choose --check-version-sync and/or --check-version-bump")
    if args.check_version_bump and not args.base:
        parser.error("--check-version-bump needs --base")
    root = Path(args.root).resolve()
    problems = check_version_sync(root)
    if args.check_version_bump:
        problems += check_version_bump(root, args.base)
    if problems:
        print("Release integrity failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print(f"Release integrity: {len(VERSION_MANIFESTS)} manifests in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
