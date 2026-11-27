#!/usr/bin/env python3
"""Check that every skill ships a well-formed scenario suite.

Usage:
    python scripts/eval_lint.py --root .

A suite is skills/<skill>/evals/evals.json: the skill's name, a note on how to run it, and a
list of scenarios, each with an id, a name, a prompt and the expectations a grader checks.
A scenario may carry tags, and a "discovery" block naming the skills a naive prompt must and
must not select. This script checks structure only; behaviour is graded by running the
scenarios, which needs a model and is not part of CI. Dev tooling only. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _scenario_problems(scenario: object, skills: set[str], seen: set[object]) -> list[str]:
    if not isinstance(scenario, dict):
        return ["a scenario is not an object"]
    label = f"scenario {scenario.get('id', '?')}"
    problems: list[str] = []
    if not isinstance(scenario.get("id"), int):
        problems.append(f"{label}: id must be an integer")
    elif scenario["id"] in seen:
        problems.append(f"{label}: duplicate id")
    seen.add(scenario.get("id"))
    for key in ("scenario", "prompt"):
        if not _is_text(scenario.get(key)):
            problems.append(f"{label}: {key} must be non-empty text")
    expectations = scenario.get("expectations")
    if (
        not isinstance(expectations, list)
        or not expectations
        or not all(map(_is_text, expectations))
    ):
        problems.append(f"{label}: expectations must be a non-empty list of text")
    tags = scenario.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) and KEBAB.match(t) for t in tags):
        problems.append(f"{label}: tags must be lower-kebab-case strings")
    discovery = scenario.get("discovery")
    if discovery is not None:
        if not isinstance(discovery, dict) or set(discovery) != {"must_select", "must_not_select"}:
            problems.append(f"{label}: discovery needs must_select and must_not_select")
        else:
            for key, names in discovery.items():
                unknown = (
                    [n for n in names if n not in skills] if isinstance(names, list) else [key]
                )
                problems.extend(f"{label}: discovery names unknown skill {n!r}" for n in unknown)
    return problems


def find_problems(root: Path) -> list[str]:
    """Return one line per problem; empty when every skill has a well-formed suite."""
    skills_dir = root / "skills"
    skills = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    problems: list[str] = []
    for skill in sorted(skills):
        where = f"skills/{skill}/evals/evals.json"
        path = skills_dir / skill / "evals" / "evals.json"
        if not path.is_file():
            problems.append(f"skills/{skill}: no evals/evals.json")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as error:
            problems.append(f"{where}: not valid JSON ({error})")
            continue
        if not isinstance(data, dict):
            problems.append(f"{where}: the suite must be an object")
            continue
        if data.get("skill_name") != skill:
            problems.append(
                f"{where}: skill_name is {data.get('skill_name')!r}, expected {skill!r}"
            )
        if not _is_text(data.get("harness")):
            problems.append(f"{where}: harness must say how the suite is run")
        scenarios = data.get("evals")
        if not isinstance(scenarios, list) or not scenarios:
            problems.append(f"{where}: evals must be a non-empty list")
            continue
        seen: set[object] = set()
        for scenario in scenarios:
            problems.extend(f"{where}: {p}" for p in _scenario_problems(scenario, skills, seen))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    problems = find_problems(Path(args.root).resolve())
    if problems:
        print(f"Scenario suites failed ({len(problems)} problem(s)):")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("Scenario suites: well formed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
