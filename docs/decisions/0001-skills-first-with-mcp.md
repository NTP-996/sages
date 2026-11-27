# 1. Skills first, with an MCP server over the same files

Date: 2026-11-27 · Status: accepted

## Context

The portrayals should be usable from any AI tool. Three shapes were considered: a skills plugin
with one manifest per harness (the shape of agent-data/job-search), an MCP server only, or both.

## Decision

Both, from one content tree. `skills/` is the only copy of the portrayals and passages. Each
harness gets a thin manifest pointing at it. The MCP server reads the same files as package data.
No manifest starts the MCP server: a plugin install needs nothing to run.

## Consequences

- Nine harnesses and any Agent Plugins client load the skills with no runtime.
- Tools without skills get the same content through MCP, plus `verify_quote`.
- Two surfaces to keep working, held together by one tree and by tests that load it from both.
- An MCP-only design was rejected: a portrayal would arrive through a tool call instead of
  loading as a skill, every machine would need a runtime, and plugin marketplaces would not list it.
