"""The documentation tells the truth about the tree, and the Hermes profile script behaves."""

import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest
import quote_guard
import verify_passages

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
SCRIPT = ROOT / "scripts" / "hermes-sage-profiles.sh"
DOCS = [
    "README.md",
    "ARCHITECTURE.md",
    "AGENTS.md",
    "CLAUDE.md",
    "COPILOT.md",
    "CONTRIBUTING.md",
    "TESTING.md",
    "CHANGELOG.md",
    "INSTALL_FOR_HERMES.md",
    "after-install.md",
    "GEMINI.md",
    ".opencode/INSTALL.md",
    "docs/PUBLISHING.md",
    "docs/decisions/0001-skills-first-with-mcp.md",
    "docs/decisions/0002-quotation-integrity.md",
    "docs/decisions/0003-modern-figures.md",
    ".github/SECURITY.md",
    "sources/PROVENANCE.md",
]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
PROFILES = ["laozi", "buddha", "confucius", "epictetus", "marcus", "jung", "munger"]


def test_readme_install_sections_lead_with_claude_hermes_and_chatgpt() -> None:
    installation = README.split("\n## Installation\n", 1)[1].split("\n## ", 1)[0]
    sections = re.findall(r"^### (.+)$", installation, re.MULTILINE)
    assert sections[:3] == ["Claude", "Hermes Agent", "ChatGPT"]
    for product in (
        "Cursor",
        "Gemini CLI",
        "GitHub Copilot CLI",
        "Factory Droid",
        "Pi",
        "opencode",
        "Any MCP client",
    ):
        assert product in sections, product


def test_readme_names_every_skill() -> None:
    for skill in (ROOT / "skills").iterdir():
        assert f"`{skill.name}`" in README, skill.name


def test_readme_quotes_only_verified_passages() -> None:
    known = set()
    for path in (ROOT / "skills").glob("*/passages.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                known.add(verify_passages.normalise(json.loads(line)["text"]))
    for match in quote_guard.QUOTED.finditer(README):
        span = match.group(1) or match.group(2)
        if len(span.split()) > quote_guard.MAX_FREE_QUOTE_WORDS:
            assert verify_passages.normalise(span) in known, span


def test_readme_passage_count_is_measured() -> None:
    total, problems = verify_passages.verify(ROOT)
    assert problems == []
    assert f"# {total} passages verified" in README
    assert f"{total} passages" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("document", DOCS)
def test_every_relative_link_resolves(document: str) -> None:
    path = ROOT / document
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        assert resolved.exists(), f"{document}: broken link {target}"


def test_changelog_has_the_current_version() -> None:
    version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))[
        "version"
    ]
    assert f"## [{version}]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_hermes_guide_installs_the_clean_branch() -> None:
    guide = (ROOT / "INSTALL_FOR_HERMES.md").read_text(encoding="utf-8")
    assert "--branch hermes https://github.com/NTP-996/sages" in guide
    assert "hermes plugins enable sages" in guide and "Ask the user before" in guide


def stub_hermes(tmp_path: Path) -> dict[str, str]:
    """A fake `hermes` on PATH that records its arguments and succeeds."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "hermes"
    fake.write_text(f'#!/bin/sh\necho "$@" >> "{tmp_path}/calls.log"\n', encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    return {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "SAGES_HERMES_ROOT": str(tmp_path / "home"),
    }


def run_script(env: dict[str, str], *args: str) -> str:
    result = subprocess.run(
        ["sh", str(SCRIPT), *args], capture_output=True, text=True, env=env, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_profile_script_table_matches_the_roster() -> None:
    pairs = re.search(r'^TEACHERS="([^"]+)"', SCRIPT.read_text(encoding="utf-8"), re.MULTILINE)
    assert pairs
    roster = json.loads((ROOT / "skills/sages/roster.json").read_text(encoding="utf-8"))
    assert pairs.group(1).split() == [
        f"{entry['hermes_profile']}:{entry['id']}" for entry in roster
    ]


def test_profile_script_dry_run_lists_seven_profiles_and_changes_nothing(tmp_path: Path) -> None:
    env = stub_hermes(tmp_path)
    output = run_script(env, "--dry-run")
    assert [
        line.split(":")[0] for line in output.splitlines() if "would create" in line
    ] == PROFILES
    assert not (tmp_path / "home").exists() and not (tmp_path / "calls.log").exists()


def test_profile_script_writes_the_portrayal_once(tmp_path: Path) -> None:
    env = stub_hermes(tmp_path)
    run_script(env)
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert [call.split()[2] for call in calls] == PROFILES and all(
        "--no-skills" in call for call in calls
    )
    soul = tmp_path / "home" / "profiles" / "epictetus" / "SOUL.md"
    text = soul.read_text(encoding="utf-8")
    assert text.startswith("# Epictetus") and "description:" not in text
    assert "portrayal-contract:start" in text
    assert (soul.parent / "passages.jsonl").is_file()

    soul.write_text(text + "\nMy own note.\n", encoding="utf-8")
    again = run_script(env)
    assert "epictetus: SOUL.md already holds the portrayal" in again
    assert "My own note." in soul.read_text(encoding="utf-8")
    run_script(env, "--force")
    assert "My own note." not in soul.read_text(encoding="utf-8")
