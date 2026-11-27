"""Every manifest carries the same version."""

import shutil
from pathlib import Path

import check_release_integrity

ROOT = Path(__file__).resolve().parents[1]


def copy_manifests(tmp_path: Path) -> Path:
    for relative in check_release_integrity.VERSION_MANIFESTS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return tmp_path


def test_the_tree_is_in_sync() -> None:
    assert check_release_integrity.check_version_sync(ROOT) == []


def test_every_version_bearing_file_is_checked() -> None:
    names = {path.as_posix() for path in check_release_integrity.VERSION_MANIFESTS}
    assert names == {
        "plugin.json",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        ".factory-plugin/plugin.json",
        "gemini-extension.json",
        "package.json",
        "plugin.yaml",
        "pyproject.toml",
        "server.json",
    }


def test_a_json_manifest_out_of_step_is_named(tmp_path: Path) -> None:
    root = copy_manifests(tmp_path)
    path = root / "gemini-extension.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace('"0.1.0"', '"0.2.0"'), encoding="utf-8"
    )
    problems = check_release_integrity.check_version_sync(root)
    assert len(problems) == 1 and "gemini-extension.json" in problems[0] and "0.2.0" in problems[0]


def test_yaml_and_toml_versions_are_read_too(tmp_path: Path) -> None:
    root = copy_manifests(tmp_path)
    for name in ("plugin.yaml", "pyproject.toml"):
        path = root / name
        path.write_text(
            path.read_text(encoding="utf-8").replace("0.1.0", "9.9.9", 1), encoding="utf-8"
        )
    problems = check_release_integrity.check_version_sync(root)
    assert {p.split(":")[0] for p in problems} == {"plugin.yaml", "pyproject.toml"}


def test_server_json_package_version_must_match(tmp_path: Path) -> None:
    root = copy_manifests(tmp_path)
    path = root / "server.json"
    text = path.read_text(encoding="utf-8")
    head, tail = text.split('"packages"', 1)
    path.write_text(head + '"packages"' + tail.replace('"0.1.0"', '"0.0.9"', 1), encoding="utf-8")
    problems = check_release_integrity.check_version_sync(root)
    assert any("server.json" in p and "0.0.9" in p for p in problems)


def test_a_missing_manifest_is_reported(tmp_path: Path) -> None:
    root = copy_manifests(tmp_path)
    (root / "plugin.json").unlink()
    assert any("plugin.json" in p for p in check_release_integrity.check_version_sync(root))


def test_non_semver_is_rejected(tmp_path: Path) -> None:
    root = copy_manifests(tmp_path)
    path = root / "package.json"
    path.write_text(path.read_text(encoding="utf-8").replace('"0.1.0"', '"v0.1"'), encoding="utf-8")
    assert any("not semver" in p for p in check_release_integrity.check_version_sync(root))
