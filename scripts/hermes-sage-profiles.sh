#!/bin/sh
# Create one Hermes Agent profile per teacher, so that each is his own agent with his own
# memory: `epictetus chat`, `laozi chat`, and so on.
#
#   sh scripts/hermes-sage-profiles.sh [--plugin-dir DIR] [--dry-run] [--force]
#
#   --plugin-dir DIR  where the Sages skills are (default: the folder above this script)
#   --dry-run         print what would happen and change nothing
#   --force           replace a SOUL.md that already exists
#
# For each teacher this creates the profile if it is missing (with no bundled skills, so the
# teacher stays a teacher) and writes the teacher's portrayal as the profile's SOUL.md, with
# his verified passages beside it. Running it again changes nothing unless --force is given.
set -eu

PLUGIN_DIR=$(cd "$(dirname "$0")/.." && pwd)
HERMES_ROOT=${SAGES_HERMES_ROOT:-$HOME/.hermes}
DRY_RUN=0
FORCE=0
# profile:skill - the same pairs as hermes_profile in skills/sages/roster.json
TEACHERS="laozi:laozi buddha:buddha confucius:confucius epictetus:epictetus marcus:marcus-aurelius jung:jung munger:munger"

while [ $# -gt 0 ]; do
  case "$1" in
    --plugin-dir) PLUGIN_DIR=$2; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

command -v hermes >/dev/null 2>&1 || { echo "hermes is not on PATH" >&2; exit 1; }

describe() {
  case "$1" in
    laozi) echo "Laozi, voice of the Tao Te Ching. Counsel on forcing less and wanting less." ;;
    buddha) echo "The Buddha of the early discourses. Counsel on suffering and the way out of it." ;;
    confucius) echo "Confucius of the Analects. Counsel on duty, learning and how to treat people." ;;
    epictetus) echo "Epictetus the Stoic teacher. Sorts what is up to you from what is not." ;;
    marcus) echo "Marcus Aurelius of the Meditations. Counsel on duty, change and the long view." ;;
    jung) echo "Carl Jung. A depth-psychology lens on dreams and patterns. Not therapy." ;;
    munger) echo "Charlie Munger. Inversion, incentives, circle of competence. No investment advice." ;;
  esac
}

for pair in $TEACHERS; do
  profile=${pair%%:*}
  skill=${pair#*:}
  source_dir="$PLUGIN_DIR/skills/$skill"
  home="$HERMES_ROOT/profiles/$profile"
  [ -f "$source_dir/SKILL.md" ] || { echo "missing $source_dir/SKILL.md" >&2; exit 1; }

  if [ -d "$home" ]; then
    echo "$profile: profile exists"
  elif [ "$DRY_RUN" -eq 1 ]; then
    echo "$profile: would create the profile"
  else
    hermes profile create "$profile" --no-skills --description "$(describe "$profile")" >/dev/null
    echo "$profile: profile created"
  fi

  if [ -f "$home/SOUL.md" ] && [ "$FORCE" -eq 0 ] && grep -q "portrayal-contract:start" "$home/SOUL.md" 2>/dev/null; then
    echo "$profile: SOUL.md already holds the portrayal (use --force to replace it)"
  elif [ "$DRY_RUN" -eq 1 ]; then
    echo "$profile: would write SOUL.md from skills/$skill/SKILL.md"
  else
    mkdir -p "$home"
    # The portrayal is the skill without its frontmatter block.
    awk 'BEGIN{fm=0} /^---$/ && fm<2 {fm++; next} fm>=2 {print}' "$source_dir/SKILL.md" > "$home/SOUL.md"
    cp "$source_dir/passages.jsonl" "$home/passages.jsonl"
    echo "$profile: SOUL.md written"
  fi
done
