# Security

## What this project runs

- The skills are markdown and data. A plugin install runs nothing.
- The Hermes adapter (`__init__.py`) registers skill files and does nothing else.
- The opencode shim adds one folder to the skill search path.
- The MCP server reads files that ship with it. It makes no network request and no model call,
  reads no secret, and writes nothing. Sage names are resolved against a fixed roster before any
  file is opened.
- The scripts under `scripts/` are development tools. Those that download fetch only from the
  URLs recorded in `sources/PROVENANCE.md` or in a passage's `source_url`, over https.

## Reporting a problem

Open a [security advisory](https://github.com/NTP-996/sages/security/advisories/new) for anything
exploitable. For a wrong or fabricated quotation, open an ordinary issue: that is the kind of
bug this project most wants to hear about.
