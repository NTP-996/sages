"""Text normalisation used for matching quotations."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_NOT_WORD = re.compile(r"[^\w\s]|_", re.UNICODE)


def normalise(text: str) -> str:
    """NFC, with each whitespace run collapsed to one space."""
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFC", text)).strip()


def loose(text: str) -> str:
    """Case-folded, punctuation removed, whitespace collapsed: for forgiving comparison."""
    return _WHITESPACE.sub(
        " ", _NOT_WORD.sub(" ", unicodedata.normalize("NFC", text).casefold())
    ).strip()


def words(text: str) -> list[str]:
    """The words of text after loose normalisation."""
    return loose(text).split()
