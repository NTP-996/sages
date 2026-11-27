"""MCP prompts: one per teacher and one for the council. The user picks these from a menu."""

from __future__ import annotations

from collections.abc import Callable

from mcp.server import MCPServer

from sages_mcp.services import SageService

ADOPT = "Adopt this portrayal from your next reply, and keep to it until I ask you to stop."


def _persona_prompt(sages: SageService, sage_id: str) -> Callable[[str], str]:
    def prompt(question: str = "") -> str:
        text = f"{ADOPT}\n\n{sages.persona(sage_id).instructions}"
        if question.strip():
            text += f"\n\nMy question: {question.strip()}"
        return text

    return prompt


def register(mcp: MCPServer, sages: SageService) -> None:
    """Attach a prompt for each teacher (hyphens become underscores) and one for the council."""
    for sage in sages.list():
        mcp.prompt(
            name=sage.id.replace("-", "_"),
            title=f"Talk with {sage.name}",
            description=f"Speak as {sage.name}. {sage.one_line}",
        )(_persona_prompt(sages, sage.id))

    @mcp.prompt(
        name="council",
        title="Ask the council",
        description="Put one question to all seven teachers and see where they agree and differ.",
    )
    def council(question: str) -> str:
        brief = sages.council(question, None)
        voices = "\n\n".join(
            f"----- {voice.sage.name} -----\n\n{voice.instructions}" for voice in brief.voices
        )
        return (
            f"{brief.protocol}\n\nThe teachers' own instructions follow.\n\n{voices}\n\n"
            f"My question for the council: {brief.question}"
        )
