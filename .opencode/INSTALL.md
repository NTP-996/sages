# Installing Sages for opencode

## Install

Add Sages to the `plugin` array in `~/.config/opencode/opencode.json` (every project) or in an
`opencode.json` at a project root (that project only):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["sages@git+https://github.com/NTP-996/sages.git"]
}
```

If the file already lists plugins, add this entry to the existing array. Restart opencode. It
installs the repository as a package and loads `.opencode/plugins/sages.js`, which adds the
`skills/` folder of that package to the skill search paths. Nothing else is configured and
nothing runs in the background.

Then say:

> Who are the sages?

## Check that it loaded

```bash
opencode run --print-logs "Use the sages skill to list the teachers."
```

The log must not contain `failed to load plugin`.

## Pin or update

opencode keeps package plugins under `~/.cache/opencode/packages/` and may reuse a cached copy of
a moving branch. To pin a version, add a commit to the entry:

```json
{ "plugin": ["sages@git+https://github.com/NTP-996/sages.git#<commit-sha>"] }
```

To update, change that commit, or delete the package's folder under
`~/.cache/opencode/packages/` and restart.

## From a local clone

```bash
git clone https://github.com/NTP-996/sages
cd sages
opencode
```

opencode loads `.opencode/plugins/sages.js` from the clone and registers its skills.
