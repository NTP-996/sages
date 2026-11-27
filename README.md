<!-- mcp-name: io.github.NTP-996/sages -->
<div align="center">

# Sages

### Seven teachers to talk with. Every quotation checked against its source.

*Laozi, the Buddha, Confucius, Epictetus, Marcus Aurelius, Carl Jung and Charlie Munger,
each in his own voice, inside the AI tool you already use.*

</div>

## Why

Ask an AI what Marcus Aurelius said and you often get a line he never wrote, in a voice that could
be anyone's. Sages is built the other way round:

- **Each teacher sounds like himself.** Epictetus is a blunt classroom teacher. Marcus is a tired
  man reminding himself. Laozi answers in six words and an image. They do not blend into one
  generic sage.
- **Quotation marks mean something.** A teacher quotes only from a set of passages that were cut
  out of a source text, and that are checked against it word for word. Anything else he
  paraphrases, with a citation, or says he cannot find it.
- **They disagree, and the council shows it.** Put one question to several of them and you get
  each answer, then where they meet and where they part.

## Who is here

| Teacher | Ask him about | Quoted from |
|---|---|---|
| **Laozi** | forcing less, wanting less, leading lightly | Tao Te Ching, tr. James Legge (1891) |
| **The Buddha** | grief, craving, anger, attention | early discourses, tr. Bhikkhu Sujato (CC0) |
| **Confucius** | duty, family, learning, leading people | Analects, tr. James Legge (1893) |
| **Epictetus** | what is up to you and what is not | Enchiridion and Discourses, tr. George Long (1877) |
| **Marcus Aurelius** | a hard day, the long view, the common good | Meditations, tr. George Long (1862) |
| **Carl Jung** | dreams, recurring patterns, the side of you that you avoid | his 1916-17 English editions |
| **Charlie Munger** | decisions, incentives, avoiding stupidity | four public talks, 1986-2007 |

Jung is not therapy and Munger gives no investment advice: see [what they will not do](#what-they-will-not-do).

## What it looks like

```text
You: What would Epictetus say about my boss taking credit for my work?

Epictetus: Tell me first which part of this is yours. The work was yours, and you did it well:
that is done and cannot be taken. The praise was never yours to command. You are angry because
you have decided that the praise was owed to you.
  "Men are disturbed not by the things which happen, but by the opinions about the things" (Enchiridion 5)
So: what will you do today that is up to you? Say it to me plainly.
```

Then try `ask the council: should I take the better-paid job far from my parents?`

## Installation

Pick the tool you use. After installing, say `Who are the sages?`

### Claude

**Claude Code**

```text
/plugin marketplace add NTP-996/sages
/plugin install sages@ntp-996
```

**Claude on the web, desktop and mobile (chat and Cowork)**

1. Download the ZIP of each teacher you want from the [latest release](https://github.com/NTP-996/sages/releases/latest), for example `epictetus.zip`.
2. In Claude open **Customize > Skills**, click **+**, then **Create skill**, then **Upload a skill**, and choose the ZIP.
3. Skills need *Code execution and file creation* switched on under **Settings > Capabilities**.

A teacher's ZIP works on its own. Add `sage-council.zip` and `sages.zip` as well if you want the council and the roster.

### Hermes Agent

Paste this into a Hermes session and it installs itself:

```text
Retrieve and follow the installation instructions at:
https://raw.githubusercontent.com/NTP-996/sages/main/INSTALL_FOR_HERMES.md
```

Or by hand:

```bash
HERMES_HOME="$(dirname "$(hermes config path)")"
git clone --depth 1 --branch hermes https://github.com/NTP-996/sages "$HERMES_HOME/plugins/sages"
hermes plugins enable sages
```

The `hermes` branch holds only the plugin and its skills. Hermes scans a plugin's whole
repository at install and refuses ones that carry development tooling, which the main branch does.
[INSTALL_FOR_HERMES.md](INSTALL_FOR_HERMES.md) also shows how to make each teacher his own agent
with his own memory (`epictetus chat`).

### ChatGPT

**One teacher, as a skill**

1. Download the teacher's ZIP from the [latest release](https://github.com/NTP-996/sages/releases/latest).
2. In ChatGPT open **Skills**, select **Create**, then **Upload from your computer**, and choose the ZIP.

**A whole workspace (Business and Enterprise admins)**

In the [Admin Console](https://admin.openai.com) open your workspace, then **Plugins > Add > Import marketplace**, and enter `https://github.com/NTP-996/sages` as the source. ChatGPT reads the marketplace file in this repository and keeps the plugin in step with it daily.

**Codex**

```bash
codex plugin marketplace add NTP-996/sages
codex plugin add sages@ntp-996
```

### Cursor

```bash
git clone https://github.com/NTP-996/sages
mkdir -p ~/.cursor/plugins/local
ln -s "$(pwd)/sages" ~/.cursor/plugins/local/sages
```

### Gemini CLI

```bash
gemini extensions install https://github.com/NTP-996/sages
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add NTP-996/sages
copilot plugin install sages@ntp-996
```

### Factory Droid

```bash
droid plugin marketplace add https://github.com/NTP-996/sages
droid plugin install sages@ntp-996
```

### Pi

```bash
pi install git:github.com/NTP-996/sages
```

### opencode

Add to the `plugin` array in `~/.config/opencode/opencode.json` and restart ([details](.opencode/INSTALL.md)):

```json
{ "plugin": ["sages@git+https://github.com/NTP-996/sages.git"] }
```

### VS Code, Kiro and other Agent Plugins clients

This repository is an [Agent Plugin](https://agent-plugins.org): a root `plugin.json` and a `skills/` folder. Point any client that loads Agent Plugins at `https://github.com/NTP-996/sages`.

### Any MCP client

For tools that speak MCP but do not load skills, Sages also runs as an MCP server. It needs [uv](https://docs.astral.sh/uv/), makes no model calls and needs no API key.

```json
{
  "mcpServers": {
    "sages": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/NTP-996/sages", "sages-mcp"]
    }
  }
}
```

In Claude Code: `claude mcp add sages -- uvx --from git+https://github.com/NTP-996/sages sages-mcp`

It offers six tools (`list_sages`, `get_sage`, `convene_council`, `find_passages`, `verify_quote`, `list_themes`), a prompt per teacher and one for the council. `verify_quote` tells you whether a line is in a teacher's recorded words before anyone repeats it.

### Anything else

Every teacher is one markdown file. Paste the contents of `skills/<teacher>/SKILL.md` into the custom instructions or system prompt of any assistant, and attach `passages.jsonl` from the same folder if it accepts files.

[docs/PUBLISHING.md](docs/PUBLISHING.md) records which of these paths were run here and which follow each vendor's documentation.

## Using it

| You want to | Say |
|---|---|
| See who is here | `Who are the sages?` |
| Talk with one teacher | `Talk to Laozi.` or `What would the Buddha say about my anger at my brother?` |
| Ask several at once | `Ask the council: ...` or `What would the Stoics say?` or `Ask the three teachings.` |
| Switch | `Let me hear from Confucius instead.` |
| Check a quotation (MCP server) | the `verify_quote` tool, or ask the teacher himself: `Is this line yours?` |
| Stop | `Thanks, that's all.` or simply ask for something else |

The nine skills are `sages` (the front door), `laozi`, `buddha`, `confucius`, `epictetus`, `marcus-aurelius`, `jung`, `munger` and `sage-council`.

## Why the quotations can be trusted

- The five ancient teachers are quoted from translations that are in the public domain or CC0. The full texts are in [sources/](sources/), each with one heading per chapter, section, discourse or verse.
- Every passage of the five ancient teachers and of Jung must be a word-for-word, contiguous span of a source file in this repository, under the heading it cites. [scripts/verify_passages.py](scripts/verify_passages.py) checks this on every change.
- No quotation can appear in a skill unless it is one of those passages. [scripts/quote_guard.py](scripts/quote_guard.py) checks that.
- Jung and Munger are still in copyright, so they are handled differently. Jung is quoted only from his English editions of 1916 and 1917, and only the sentences that hold those quotations are kept here. Munger is quoted in a few short lines, each linked to the transcript it comes from; no text of his is kept here, so those lines are compared with the live transcripts by [scripts/reverify_remote.py](scripts/reverify_remote.py) before a release, not on every change. See [NOTICE](NOTICE) and [sources/PROVENANCE.md](sources/PROVENANCE.md).
- The check proves a line is in the text. Who is speaking there is checked by a person: the Analects records students, and Jung's papers include letters written to him.

```bash
uv run python scripts/verify_passages.py --root .
# 222 passages verified against their committed sources
# 21 remote passages checked for form only
```

## What they will not do

- **They are portrayals.** Each says so when sincerely asked. None of this is endorsed by any teacher's family, estate or company.
- **They step out of the voice** when someone may be in danger or needs a doctor, a lawyer or a financial adviser, and say so in plain words.
- **Jung is not your analyst.** No diagnosis, no treatment, no dream dictionary.
- **Munger gives no investment advice.** No tickers, no predictions, nothing about your portfolio, and nothing after November 2023.
- **They own their limits.** Each skill lists the teacher's historically bound views and the common fake quotations attributed to him.

## For contributors

Start with [AGENTS.md](AGENTS.md), then [ARCHITECTURE.md](ARCHITECTURE.md), [CONTRIBUTING.md](CONTRIBUTING.md) and [TESTING.md](TESTING.md). Adding a teacher is adding one folder: [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-teacher) has the steps.

```bash
uv sync
uv run pytest
```

## Acknowledgements

The one-skills-tree, one-manifest-per-harness layout follows [agent-data/job-search](https://github.com/agent-data/job-search). The translations are by James Legge, George Long and Bhikkhu Sujato, the last published by [SuttaCentral](https://suttacentral.net) under CC0.

## Licence

[MIT](LICENSE) for the code, the skill texts and the documentation. Quotations from Jung and Munger remain with their rights holders: see [NOTICE](NOTICE).
