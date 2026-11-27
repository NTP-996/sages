"""Hermes Agent plugin adapter for Sages.

Hermes imports this file when the enabled plugin loads and calls register(ctx). It checks
that the installed tree is complete, then registers the nine skills, which Hermes lists as
sages:<skill>, each with the description from its own frontmatter.

This adapter is for Hermes only and does nothing anywhere else. It uses the standard library
only, never edits Hermes configuration, and registers no tools, hooks or commands.
"""

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent

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


def _description(skill_md: Path) -> str:
    """Return the description from a SKILL.md frontmatter block, or an empty string."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ""
    for line in text[4 : text.find("\n---", 4)].splitlines():
        if line.startswith("description:"):
            value = line[len("description:") :].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            return value
    return ""


def register(ctx: Any) -> None:
    missing = [
        f"skills/{name}/SKILL.md"
        for name in SKILLS
        if not (REPO_ROOT / "skills" / name / "SKILL.md").is_file()
    ]
    if missing:
        raise RuntimeError(
            "sages plugin install is incomplete - missing: "
            + ", ".join(missing)
            + ". Remove this directory and clone it again: git clone --depth 1 --branch hermes "
            "https://github.com/NTP-996/sages <HERMES_HOME>/plugins/sages "
            "(see INSTALL_FOR_HERMES.md)."
        )
    for name in SKILLS:
        skill_md = REPO_ROOT / "skills" / name / "SKILL.md"
        ctx.register_skill(name, skill_md, _description(skill_md))
