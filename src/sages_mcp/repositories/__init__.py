"""Data access. Services depend on the Protocols, never on the filesystem classes."""

from sages_mcp.repositories.sage_repository import FileSageRepository, SageRepository
from sages_mcp.repositories.source_repository import FileSourceRepository, SourceRepository

__all__ = ["FileSageRepository", "FileSourceRepository", "SageRepository", "SourceRepository"]
