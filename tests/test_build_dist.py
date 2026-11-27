"""Release artefacts: one ZIP per skill for chat apps, and a clean tree for Hermes Agent."""

import importlib.util
import zipfile
from pathlib import Path

import build_dist
from test_skills import PERSONAS

ROOT = Path(__file__).resolve().parents[1]
ALL_SKILLS = {*PERSONAS, "sages", "sage-council"}
HERMES_FILES = {
    "plugin.yaml",
    "__init__.py",
    "after-install.md",
    "INSTALL_FOR_HERMES.md",
    "LICENSE",
    "NOTICE",
    "README.md",
}


def test_one_zip_per_skill_holding_only_what_the_skill_needs(tmp_path: Path) -> None:
    written = build_dist.build_skill_zips(ROOT, tmp_path)
    assert {path.name for path in written} == {f"{skill}.zip" for skill in ALL_SKILLS}
    names = set(zipfile.ZipFile(tmp_path / "epictetus.zip").namelist())
    assert names == {"epictetus/SKILL.md", "epictetus/passages.jsonl"}
    assert set(zipfile.ZipFile(tmp_path / "sage-council.zip").namelist()) == {
        "sage-council/SKILL.md"
    }
    assert set(zipfile.ZipFile(tmp_path / "sages.zip").namelist()) == {
        "sages/SKILL.md",
        "sages/roster.json",
    }


def test_zips_are_reproducible(tmp_path: Path) -> None:
    build_dist.build_skill_zips(ROOT, tmp_path / "a")
    build_dist.build_skill_zips(ROOT, tmp_path / "b")
    assert (tmp_path / "a" / "jung.zip").read_bytes() == (tmp_path / "b" / "jung.zip").read_bytes()


def test_hermes_tree_holds_the_plugin_and_nothing_a_scanner_would_flag(tmp_path: Path) -> None:
    out = build_dist.build_hermes_tree(ROOT, tmp_path / "hermes")
    top = {path.name for path in out.iterdir()}
    assert top == {*HERMES_FILES, "skills"}
    relative = {path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file()}
    assert not any(
        part in name
        for name in relative
        for part in ("evals/", "tests/", "scripts/", "sources/", ".github")
    )
    assert not any(name.endswith((".py", ".sh", ".js")) for name in relative - {"__init__.py"})
    assert {f"skills/{skill}/SKILL.md" for skill in ALL_SKILLS} <= relative


def test_the_adapter_in_the_hermes_tree_registers_the_nine_skills(tmp_path: Path) -> None:
    out = build_dist.build_hermes_tree(ROOT, tmp_path / "hermes")
    spec = importlib.util.spec_from_file_location("hermes_tree_adapter", out / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    registered: list[str] = []

    class Ctx:
        def register_skill(self, name: str, path: Path, description: str = "") -> None:
            assert Path(path).is_file() and description
            registered.append(name)

    module.register(Ctx())
    assert set(registered) == ALL_SKILLS


def test_building_twice_replaces_the_tree(tmp_path: Path) -> None:
    out = build_dist.build_hermes_tree(ROOT, tmp_path / "hermes")
    (out / "stale.txt").write_text("old", encoding="utf-8")
    build_dist.build_hermes_tree(ROOT, tmp_path / "hermes")
    assert not (out / "stale.txt").exists()


def test_cli_writes_both(tmp_path: Path) -> None:
    code = build_dist.main(
        ["--root", str(ROOT), "--zips", str(tmp_path / "z"), "--hermes", str(tmp_path / "h")]
    )
    assert (
        code == 0
        and (tmp_path / "z" / "buddha.zip").is_file()
        and (tmp_path / "h" / "plugin.yaml").is_file()
    )
