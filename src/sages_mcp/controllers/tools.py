"""MCP tools."""

from __future__ import annotations

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from sages_mcp.controllers import passage_dict, sage_dict
from sages_mcp.services import PassageService, SageService, UnknownSageError

HOW_TO_USE = (
    "Follow these instructions from your next reply until the person asks you to stop. Put "
    "quotation marks only around a passage returned by find_passages, or one for which "
    'verify_quote returned "verified".'
)


def register(mcp: MCPServer, sage_service: SageService, passage_service: PassageService) -> None:
    """Attach the six tools to the server."""

    @mcp.tool()
    def list_sages() -> list[dict[str, object]]:
        """List the seven teachers, in council order, with one line on what each is good for."""
        return [sage_dict(sage) for sage in sage_service.list()]

    @mcp.tool()
    def get_sage(sage: str) -> dict[str, object]:
        """Get the instructions for speaking as one teacher.

        Args:
            sage: A teacher's id, name or common alias, for example "epictetus", "Lao Tzu"
                or "Marcus Aurelius".
        """
        try:
            persona = sage_service.persona(sage)
        except UnknownSageError as error:
            raise ToolError(str(error)) from error
        return {
            **sage_dict(persona.sage),
            "instructions": persona.instructions,
            "passage_count": persona.passage_count,
            "how_to_use": HOW_TO_USE,
        }

    @mcp.tool()
    def convene_council(question: str, sages: list[str] | None = None) -> dict[str, object]:
        """Get what is needed to answer one question in several teachers' voices.

        Returns the council protocol and each chosen teacher's instructions, in council order.
        You write the answer: each voice in turn, then where they agree and where they differ.

        Args:
            question: The question to put to the council.
            sages: Teachers to include, by id, name or alias. All seven when omitted.
        """
        try:
            brief = sage_service.council(question, sages)
        except (UnknownSageError, ValueError) as error:
            raise ToolError(str(error)) from error
        return {
            "question": brief.question,
            "order": [voice.sage.id for voice in brief.voices],
            "protocol": brief.protocol,
            "voices": [
                {"id": voice.sage.id, "name": voice.sage.name, "instructions": voice.instructions}
                for voice in brief.voices
            ],
        }

    @mcp.tool()
    def find_passages(
        sage: str | None = None, theme: str | None = None, query: str | None = None, limit: int = 5
    ) -> list[dict[str, object]]:
        """Find verified quotations, each checked word for word against its source.

        Args:
            sage: Limit to one teacher (id, name or alias). All teachers when omitted.
            theme: A theme tag such as "anger", "grief", "work" or "death". See list_themes.
            query: Words that must all appear in the passage, its citation or its themes.
            limit: How many to return, from 1 to 20.
        """
        try:
            found = passage_service.find(sage=sage, theme=theme, query=query, limit=limit)
        except UnknownSageError as error:
            raise ToolError(str(error)) from error
        return [passage_dict(passage) for passage in found]

    @mcp.tool()
    def verify_quote(text: str, sage: str | None = None) -> dict[str, object]:
        """Check whether a line is a teacher's recorded words before quoting it.

        The status is "verified" (part of a verified passage: safe to quote with its citation),
        "in-source" (the words are in a bundled source text, with the section), "close" (not
        word for word; the recorded wording is returned) or "not-found".

        An "in-source" result does not check who is speaking in that section: it may be a
        student, an opponent or someone he quotes. Read the section before attributing it.

        Args:
            text: The line to check, at least six words.
            sage: Limit the check to one teacher (id, name or alias).
        """
        try:
            check = passage_service.verify_quote(text, sage)
        except UnknownSageError as error:
            raise ToolError(str(error)) from error
        return {
            "status": check.status,
            "note": check.note,
            "source_citation": check.source_citation,
            "matches": [passage_dict(passage) for passage in check.matches],
        }

    @mcp.tool()
    def list_themes() -> dict[str, int]:
        """List every theme tag with the number of verified passages that carry it."""
        return passage_service.themes()
