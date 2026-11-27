"""MCP resources: the roster, each portrayal and each teacher's verified passages."""

from __future__ import annotations

import json

from mcp.server import MCPServer

from sages_mcp.controllers import passage_dict, sage_dict
from sages_mcp.services import PassageService, SageService


def register(mcp: MCPServer, sages: SageService, passages: PassageService) -> None:
    """Attach the three resources to the server."""

    @mcp.resource(
        "sage://roster",
        name="roster",
        description="The seven teachers, in council order.",
        mime_type="application/json",
    )
    def roster() -> str:
        return json.dumps([sage_dict(sage) for sage in sages.list()], ensure_ascii=False)

    @mcp.resource(
        "sage://{sage_id}/persona",
        name="persona",
        description="The instructions for speaking as one teacher.",
        mime_type="text/markdown",
    )
    def persona(sage_id: str) -> str:
        return sages.persona(sage_id).instructions

    @mcp.resource(
        "sage://{sage_id}/passages",
        name="passages",
        description="Every verified passage of one teacher.",
        mime_type="application/json",
    )
    def teacher_passages(sage_id: str) -> str:
        found = passages.find(sage=sage_id, limit=20)
        every = found if len(found) < 20 else passages.all_for(sage_id)
        return json.dumps([passage_dict(passage) for passage in every], ensure_ascii=False)
