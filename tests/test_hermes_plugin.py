"""The Hermes Agent adapter: manifest shape and what register() does."""

import importlib.util
import json
import re
import shutil
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "plugin.yaml"
ADAPTER = ROOT / "__init__.py"
SKILLS = (
    "sages",
    "buddha",
    "laozi",
    "confucius",
    "marcus-aurelius",
    "epictetus",
    "jung",
    "munger",
    "sage-council",
)


def manifest_value(key: str) -> str:
    match = re.search(
        rf'^{key}:\s*["\']?([^"\'\n#]+?)["\']?\s*$',
        MANIFEST.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match, f"plugin.yaml has no top-level '{key}:' line"
    return match.group(1).strip()


def load_adapter(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("sages_hermes_adapter", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StubCtx:
    """Records register_skill calls; any other attribute access fails the test."""

    def __init__(self) -> None:
        self.skills: list[tuple[str, Path, str]] = []

    def register_skill(self, name: str, path: Path, description: str = "") -> None:
        self.skills.append((name, Path(path), description))

    def __getattr__(self, attribute: str) -> object:
        raise AssertionError(f"the adapter touched an unexpected ctx attribute: {attribute}")


def synthetic_tree(tmp_path: Path) -> Path:
    root = tmp_path / "sages"
    for name in SKILLS:
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: About {name}.\n---\n# {name}\n", encoding="utf-8"
        )
    shutil.copy2(ADAPTER, root / "__init__.py")
    return root


def test_manifest_fields() -> None:
    assert manifest_value("manifest_version") == "1"
    assert manifest_value("name") == "sages"
    assert manifest_value("kind") == "standalone"
    assert manifest_value("description")
    primary = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest_value("version") == primary["version"]


def test_manifest_declares_no_env_tools_or_hooks() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for key in ("requires_env", "provides_tools", "provides_hooks", "python_dependencies"):
        assert key not in text


def test_register_registers_exactly_the_shipped_skills() -> None:
    ctx = StubCtx()
    load_adapter(ADAPTER).register(ctx)
    assert [name for name, _, _ in ctx.skills] == list(SKILLS)
    assert sorted(SKILLS) == sorted(p.name for p in (ROOT / "skills").iterdir() if p.is_dir())
    for name, path, _ in ctx.skills:
        assert path == ROOT / "skills" / name / "SKILL.md" and path.is_file()


def test_register_passes_frontmatter_description() -> None:
    ctx = StubCtx()
    load_adapter(ADAPTER).register(ctx)
    described = {name: description for name, _, description in ctx.skills}
    assert described["epictetus"].startswith("Speak as Epictetus")
    assert all(len(text) > 40 for text in described.values())


def test_missing_skill_fails_naming_it_and_the_recovery(tmp_path: Path) -> None:
    root = synthetic_tree(tmp_path)
    shutil.rmtree(root / "skills" / "jung")
    with pytest.raises(RuntimeError) as error:
        load_adapter(root / "__init__.py").register(StubCtx())
    assert "skills/jung/SKILL.md" in str(error.value)
    assert "hermes plugins install NTP-996/sages --force" in str(error.value)


def test_synthetic_tree_is_a_complete_install(tmp_path: Path) -> None:
    ctx = StubCtx()
    load_adapter(synthetic_tree(tmp_path) / "__init__.py").register(ctx)
    assert [(name, description) for name, _, description in ctx.skills][0] == (
        "sages",
        "About sages.",
    )
