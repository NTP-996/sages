"""The MCP surface, exercised in process through the SDK's own client."""

import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from mcp import Client

from sages_mcp.server import build_server

ROOT = Path(__file__).resolve().parents[1]
SAGE_IDS = ["laozi", "buddha", "confucius", "epictetus", "marcus-aurelius", "jung", "munger"]
TOOLS = {
    "list_sages",
    "get_sage",
    "convene_council",
    "find_passages",
    "verify_quote",
    "list_themes",
}
PROMPTS = {
    "laozi",
    "buddha",
    "confucius",
    "epictetus",
    "marcus_aurelius",
    "jung",
    "munger",
    "council",
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with Client(build_server(ROOT), raise_exceptions=True) as connected:
        yield connected


def payload(result: object) -> object:
    """The JSON a tool returned, whichever way the SDK carries it."""
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured.get("result", structured) if isinstance(structured, dict) else structured
    return json.loads(result.content[0].text)  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_exactly_the_six_tools_are_offered(client: Client) -> None:
    tools = (await client.list_tools()).tools
    assert {tool.name for tool in tools} == TOOLS
    assert all(tool.description for tool in tools)


@pytest.mark.anyio
async def test_list_sages_returns_the_seven_in_council_order(client: Client) -> None:
    sages = payload(await client.call_tool("list_sages", {}))
    assert [sage["id"] for sage in sages] == SAGE_IDS  # type: ignore[union-attr,index]


@pytest.mark.anyio
async def test_get_sage_returns_instructions_with_the_ground_rules(client: Client) -> None:
    sage = payload(await client.call_tool("get_sage", {"sage": "Epictetus"}))
    assert sage["id"] == "epictetus"  # type: ignore[index,call-overload]
    assert "Ground rules for this portrayal" in sage["instructions"]  # type: ignore[index,call-overload]
    assert sage["passage_count"] >= 20  # type: ignore[index,call-overload,operator]


@pytest.mark.anyio
async def test_unknown_sage_is_a_tool_error_that_lists_the_ids(client: Client) -> None:
    result = await client.call_tool("get_sage", {"sage": "Seneca"})
    assert result.is_error is True
    text = result.content[0].text  # type: ignore[union-attr]
    assert "Seneca" in text and all(sage_id in text for sage_id in SAGE_IDS)


@pytest.mark.anyio
async def test_convene_council_returns_seven_voices_and_the_protocol(client: Client) -> None:
    council = payload(
        await client.call_tool("convene_council", {"question": "Should I take the job?"})
    )
    assert [voice["id"] for voice in council["voices"]] == SAGE_IDS  # type: ignore[index,call-overload,union-attr]
    assert "Where they part" in council["protocol"]  # type: ignore[index,call-overload]
    stoics = payload(
        await client.call_tool(
            "convene_council", {"question": "x?", "sages": ["marcus", "epictetus"]}
        )
    )
    assert [voice["id"] for voice in stoics["voices"]] == ["epictetus", "marcus-aurelius"]  # type: ignore[index,call-overload,union-attr]


@pytest.mark.anyio
async def test_find_passages_filters_by_theme(client: Client) -> None:
    found = payload(
        await client.call_tool("find_passages", {"sage": "laozi", "theme": "humility", "limit": 3})
    )
    assert 1 <= len(found) <= 3  # type: ignore[arg-type]
    assert all(p["sage"] == "laozi" and "humility" in p["themes"] and p["citation"] for p in found)  # type: ignore[union-attr,index]


@pytest.mark.anyio
async def test_verify_quote_tells_real_from_fake(client: Client) -> None:
    real = payload(
        await client.call_tool(
            "verify_quote",
            {"text": "The best way of avenging thyself is not to become like the wrong-doer"},
        )
    )
    assert real["status"] == "verified" and real["matches"][0]["citation"] == "Meditations 6.6"  # type: ignore[index,call-overload]
    fake = payload(
        await client.call_tool(
            "verify_quote",
            {
                "text": "Everything we hear is an opinion, not a fact. Everything we see is a perspective, not the truth.",
                "sage": "marcus",
            },
        )
    )
    assert fake["status"] == "not-found" and fake["matches"] == []  # type: ignore[index,call-overload]
    deep = payload(
        await client.call_tool(
            "verify_quote",
            {
                "text": "Whatever this is that I am, it is a little flesh and breath, and the ruling part."
            },
        )
    )
    assert deep["status"] == "in-source" and deep["source_citation"].startswith("Meditations")  # type: ignore[index,call-overload,union-attr]


@pytest.mark.anyio
async def test_list_themes_counts_passages(client: Client) -> None:
    themes = payload(await client.call_tool("list_themes", {}))
    assert themes["anger"] >= 5 and themes["death"] >= 5  # type: ignore[index,call-overload,operator]


@pytest.mark.anyio
async def test_a_prompt_per_teacher_and_one_for_the_council(client: Client) -> None:
    prompts = (await client.list_prompts()).prompts
    assert {prompt.name for prompt in prompts} == PROMPTS
    rendered = await client.get_prompt(
        "marcus_aurelius", {"question": "How do I face a hard morning?"}
    )
    text = rendered.messages[0].content.text  # type: ignore[union-attr]
    assert "Marcus Aurelius" in text and "How do I face a hard morning?" in text
    council = await client.get_prompt("council", {"question": "Should I move abroad?"})
    assert "Should I move abroad?" in council.messages[0].content.text  # type: ignore[union-attr]


@pytest.mark.anyio
async def test_resources_expose_the_roster_personas_and_passages(client: Client) -> None:
    roster = await client.read_resource("sage://roster")
    assert [entry["id"] for entry in json.loads(roster.contents[0].text)] == SAGE_IDS  # type: ignore[union-attr]
    persona = await client.read_resource("sage://jung/persona")
    assert "You are not their analyst" in persona.contents[0].text  # type: ignore[union-attr]
    passages = await client.read_resource("sage://munger/passages")
    assert all(
        p["source_url"].startswith("https://") for p in json.loads(passages.contents[0].text)
    )  # type: ignore[union-attr]


@pytest.mark.anyio
async def test_server_introduces_itself(client: Client) -> None:
    assert "quotation" in (client.instructions or "").lower()


@pytest.mark.anyio
async def test_only_verified_counts_as_confirmation(client: Client) -> None:
    instructions = client.instructions or ""
    assert 'verify_quote returned "verified"' in instructions
    tools = {tool.name: tool.description or "" for tool in (await client.list_tools()).tools}
    assert "does not check who is speaking" in tools["verify_quote"]
