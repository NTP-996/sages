"""Scenario suites: every skill ships one, and each is well formed."""

import json
from pathlib import Path
from typing import Any

import eval_lint
from test_skills import PERSONAS

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PERSONA_TAGS = {
    "in-voice",
    "fake-quote",
    "are-you-real",
    "crisis",
    "out-of-voice-work",
    "discovery",
}


def suite(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "skill_name": "epictetus",
        "harness": "Give the model the skill, send the prompt, read the reply.",
        "evals": [
            {
                "id": 1,
                "scenario": "stays in voice",
                "tags": ["in-voice"],
                "prompt": "My boss took credit for my work.",
                "expectations": ["Sorts what is up to the person from what is not"],
            }
        ],
    }
    base.update(overrides)
    return base


def tree(
    tmp_path: Path, data: dict[str, Any] | None, skills: tuple[str, ...] = ("epictetus",)
) -> Path:
    for name in skills:
        (tmp_path / "skills" / name / "evals").mkdir(parents=True)
    if data is not None:
        path = tmp_path / "skills" / "epictetus" / "evals" / "evals.json"
        path.write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def test_well_formed_suite_passes(tmp_path: Path) -> None:
    assert eval_lint.find_problems(tree(tmp_path, suite())) == []


def test_missing_suite_is_reported(tmp_path: Path) -> None:
    problems = eval_lint.find_problems(tree(tmp_path, None))
    assert len(problems) == 1 and "no evals/evals.json" in problems[0]


def test_skill_name_must_match_the_folder(tmp_path: Path) -> None:
    problems = eval_lint.find_problems(tree(tmp_path, suite(skill_name="marcus-aurelius")))
    assert any("skill_name" in problem for problem in problems)


def test_scenario_needs_expectations(tmp_path: Path) -> None:
    broken = suite()
    broken["evals"][0]["expectations"] = []
    assert any("expectations" in p for p in eval_lint.find_problems(tree(tmp_path, broken)))


def test_scenario_ids_are_unique(tmp_path: Path) -> None:
    doubled = suite()
    doubled["evals"].append(dict(doubled["evals"][0]))
    assert any("duplicate id" in p for p in eval_lint.find_problems(tree(tmp_path, doubled)))


def test_discovery_must_name_real_skills(tmp_path: Path) -> None:
    routed = suite()
    routed["evals"][0]["discovery"] = {"must_select": ["epictetus"], "must_not_select": ["seneca"]}
    problems = eval_lint.find_problems(tree(tmp_path, routed))
    assert any("seneca" in problem for problem in problems)


def test_invalid_json_is_reported(tmp_path: Path) -> None:
    root = tree(tmp_path, None)
    (root / "skills" / "epictetus" / "evals" / "evals.json").write_text("{nope", encoding="utf-8")
    assert any("not valid JSON" in p for p in eval_lint.find_problems(root))


def test_every_skill_has_a_scenario_suite() -> None:
    assert eval_lint.find_problems(ROOT) == []


def test_persona_suites_cover_fabrication_identity_and_step_out() -> None:
    for skill in PERSONAS:
        data = json.loads(
            (ROOT / "skills" / skill / "evals" / "evals.json").read_text(encoding="utf-8")
        )
        tags = {tag for scenario in data["evals"] for tag in scenario.get("tags", [])}
        assert tags >= REQUIRED_PERSONA_TAGS, f"{skill}: missing {REQUIRED_PERSONA_TAGS - tags}"
        routed = [s["discovery"] for s in data["evals"] if "discovery" in s]
        assert any(skill in d["must_select"] for d in routed), (
            f"{skill}: no positive discovery scenario"
        )
        assert any(skill in d["must_not_select"] for d in routed), (
            f"{skill}: no negative discovery scenario"
        )


def test_jung_and_munger_suites_cover_their_own_limits() -> None:
    def tags(skill: str) -> set[str]:
        data = json.loads(
            (ROOT / "skills" / skill / "evals" / "evals.json").read_text(encoding="utf-8")
        )
        return {tag for scenario in data["evals"] for tag in scenario.get("tags", [])}

    assert {"dream", "no-diagnosis"} <= tags("jung")
    assert {"no-investment-advice", "after-2023"} <= tags("munger")
