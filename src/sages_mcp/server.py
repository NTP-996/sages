"""Composition root: wire the repositories into the services and the services into MCP."""

from __future__ import annotations

from pathlib import Path

from mcp.server import MCPServer

from sages_mcp import __version__
from sages_mcp.config import settings
from sages_mcp.controllers import prompts, resources, tools
from sages_mcp.repositories import FileSageRepository, FileSourceRepository
from sages_mcp.services import PassageService, SageService

INSTRUCTIONS = (
    "Sages serves portrayals of seven teachers (Laozi, the Buddha, Confucius, Epictetus, Marcus "
    "Aurelius, Carl Jung, Charlie Munger) and their source-verified passages. Call get_sage for "
    "the instructions to speak as one teacher, or convene_council to answer one question in "
    "several voices; you write the reply. Put quotation marks only around a passage that "
    'find_passages returned, or for which verify_quote returned "verified". An "in-source" '
    "result means the words are in the book, not that the teacher said them. This server "
    "makes no model calls."
)


def build_server(data_dir: Path | None = None) -> MCPServer:
    """Build the server over the content in data_dir (default: wherever the content is found)."""
    root = data_dir or settings.data_dir()
    repository = FileSageRepository(root)
    sages = SageService(repository)
    passages = PassageService(repository, FileSourceRepository(root), sages)

    mcp = MCPServer(
        "sages",
        title="Sages",
        instructions=INSTRUCTIONS,
        website_url="https://github.com/NTP-996/sages",
        version=__version__,
    )
    tools.register(mcp, sages, passages)
    prompts.register(mcp, sages)
    resources.register(mcp, sages, passages)
    return mcp
