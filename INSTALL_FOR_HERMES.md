# Install Sages on Hermes Agent

Written for the Hermes Agent instance doing the installation. Read the whole file first, then
work the steps in order. Verified against Hermes Agent v0.23.4. If a command behaves differently
on this machine, say so in your report instead of improvising around it.

What this installs: the plugin `sages`, which registers nine skills: seven teachers (`laozi`,
`buddha`, `confucius`, `epictetus`, `marcus-aurelius`, `jung`, `munger`), the council
(`sage-council`) and the front door (`sages`). Hermes lists them as `sages:<skill>`.

## Step 1 - Confirm the environment

```bash
command -v git && command -v hermes
CONFIG="$(hermes config path)"
HERMES_HOME="$(dirname "$CONFIG")"
```

Both commands must print a path. If you are not a Hermes Agent instance with shell access, stop
and tell the user. Work only with this `HERMES_HOME`: the active profile may live under a
`profiles/` directory.

## Step 2 - Check for an existing install

```bash
test -d "$HERMES_HOME/plugins/sages" && git -C "$HERMES_HOME/plugins/sages" status --porcelain
```

- The directory is absent: continue with Step 3.
- It is present and the output is empty: go to "Updating" below.
- The output is not empty: the user has local changes. Show them and stop.

## Step 3 - Install

```bash
git clone --depth 1 --branch hermes https://github.com/NTP-996/sages "$HERMES_HOME/plugins/sages"
hermes plugins enable sages
```

Clone the `hermes` branch, not `main`. Hermes scans a plugin's whole tree when it installs one,
and the main branch carries tests, build scripts and full source texts that the scanner flags
(a line of Epictetus reads to it like an injected instruction). The `hermes` branch is generated
from main at each release and holds only the manifest, the adapter and the skills.
`hermes plugins install NTP-996/sages` therefore reports the main branch as blocked; do not
override that with `--force` unless the user asks you to.

## Step 4 - Verify

```bash
hermes plugins show sages                      # Status: enabled
hermes plugins doctor "$HERMES_HOME/plugins/sages"   # OK: ... registration passed
ls "$HERMES_HOME/plugins/sages/skills"         # nine folders
```

Hermes builds its skill list when a session starts, so tell the user to start a new session
(`/new`) and then say:

```text
Who are the sages?
```

## Step 5 - Optional: one agent per teacher

Ask the user before doing this. It creates seven Hermes profiles (`laozi`, `buddha`, `confucius`,
`epictetus`, `marcus`, `jung`, `munger`), each with the teacher's portrayal as its `SOUL.md`, so
that each teacher is his own agent with his own memory and his own command (`epictetus chat`).

```bash
curl -fsSL -o /tmp/hermes-sage-profiles.sh \
  https://raw.githubusercontent.com/NTP-996/sages/main/scripts/hermes-sage-profiles.sh
sh /tmp/hermes-sage-profiles.sh --plugin-dir "$HERMES_HOME/plugins/sages" --dry-run
sh /tmp/hermes-sage-profiles.sh --plugin-dir "$HERMES_HOME/plugins/sages"
```

Read the script and show the user the dry run before the real run. It never replaces an existing
`SOUL.md` unless `--force` is given. Remove a profile with `hermes profile delete <name>`.

## Step 6 - Report

Tell the user: where the plugin was installed, that `hermes plugins show sages` reports it
enabled, which checks you ran, whether profiles were created, and that a new session is needed.

## Updating

```bash
git -C "$HERMES_HOME/plugins/sages" fetch --depth 1 origin hermes
git -C "$HERMES_HOME/plugins/sages" reset --hard origin/hermes
```

Only when Step 2 showed no local changes. Then start a new session.

## Removing

```bash
hermes plugins remove sages
```

Profiles created in Step 5 are separate: delete each with `hermes profile delete <name>`.
