"""One skills tree, one manifest per harness: each manifest is well formed and tells the truth."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
REPO = "https://github.com/NTP-996/sages"
AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
AGENT_PLUGINS_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
PLUGIN_MANIFESTS = (
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".factory-plugin/plugin.json",
)


def load(relative: str) -> dict[str, Any]:
    data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


@pytest.mark.parametrize("relative", PLUGIN_MANIFESTS)
def test_plugin_manifest_identity(relative: str) -> None:
    manifest = load(relative)
    assert manifest["name"] == "sages"
    assert manifest["version"] == VERSION
    assert manifest["license"] == "MIT"
    assert manifest["repository"] == REPO
    assert manifest["author"]["name"] == "NTP-996"
    assert 40 <= len(manifest["description"]) <= 400


def test_agent_plugins_manifest_is_closed_and_names_its_schema() -> None:
    manifest = load("plugin.json")
    assert manifest["$schema"] == AGENT_PLUGINS_SCHEMA
    assert set(manifest) <= AGENT_PLUGINS_FIELDS, (
        "the Agent Plugins manifest allows no other top-level field"
    )
    assert re.fullmatch(r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", manifest["name"])
    assert set(manifest["author"]) <= {"name", "email", "url"}


@pytest.mark.parametrize(
    "relative",
    (".codex-plugin/plugin.json", ".cursor-plugin/plugin.json", ".factory-plugin/plugin.json"),
)
def test_manifests_that_point_at_the_skills_tree(relative: str) -> None:
    assert load(relative)["skills"] == "./skills/"


def test_claude_marketplace_lists_the_plugin_at_the_repository_root() -> None:
    marketplace = load(".claude-plugin/marketplace.json")
    assert marketplace["name"] == "ntp-996"
    assert marketplace["owner"]["name"] == "NTP-996"
    assert [(p["name"], p["source"]) for p in marketplace["plugins"]] == [("sages", ".")]


def test_gemini_extension() -> None:
    extension = load("gemini-extension.json")
    assert extension["name"] == "sages" and extension["version"] == VERSION
    assert extension["contextFileName"] == "GEMINI.md"
    context = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
    assert "skills/sages/SKILL.md" in context
    assert len(context.split()) <= 200, "GEMINI.md is loaded into every session: keep it short"


def test_package_json_serves_pi_and_opencode() -> None:
    package = load("package.json")
    assert package["name"] == "sages" and package["version"] == VERSION
    assert package["pi"] == {"skills": ["./skills"]}
    assert "pi-package" in package["keywords"]
    assert package["main"] == ".opencode/plugins/sages.js" and package["type"] == "module"
    assert (ROOT / package["main"]).is_file()
    assert "dependencies" not in package


def test_no_manifest_starts_the_mcp_server() -> None:
    """Plugin users get skills with nothing to run; the MCP server is a separate, explicit install."""
    assert not (ROOT / "mcp.json").exists() and not (ROOT / ".mcp.json").exists()
    for relative in (*PLUGIN_MANIFESTS, "gemini-extension.json", "package.json"):
        assert "mcpServers" not in (ROOT / relative).read_text(encoding="utf-8"), relative


def test_mcp_registry_entry() -> None:
    server = load("server.json")
    assert server["name"] == "io.github.NTP-996/sages"
    assert server["version"] == VERSION
    assert len(server["description"]) <= 100
    assert server["repository"] == {"url": REPO, "source": "github"}
    (package,) = server["packages"]
    assert package["registryType"] == "pypi" and package["identifier"] == "sages-mcp"
    assert package["version"] == VERSION and package["transport"] == {"type": "stdio"}


def test_descriptions_make_no_claim_the_pack_cannot_keep() -> None:
    for relative in (*PLUGIN_MANIFESTS, "gemini-extension.json", "package.json", "server.json"):
        description = load(relative)["description"].lower()
        for word in ("therapy", "investment advice"):
            assert word not in description or "no " in description or "not " in description, (
                relative
            )
