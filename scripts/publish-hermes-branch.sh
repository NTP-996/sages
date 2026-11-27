#!/bin/sh
# Replace the "hermes" branch with the tree in <dir> (built by build_dist.py --hermes) and push it.
#
#   sh scripts/publish-hermes-branch.sh dist/hermes v0.1.0
set -eu

tree=$(cd "$1" && pwd)
label=${2:-unreleased}
remote=${SAGES_REMOTE:-origin}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

url=$(git remote get-url --push "$remote")
git init -q -b hermes "$work"
cp -R "$tree"/. "$work"/
git -C "$work" add -A
git -C "$work" -c user.name="${GIT_AUTHOR_NAME:-NTP-996}" \
  -c user.email="${GIT_AUTHOR_EMAIL:-31298991+NTP-996@users.noreply.github.com}" \
  commit -q -m "build: Hermes Agent tree for $label"
git -C "$work" push -q --force "$url" hermes:hermes
echo "hermes branch published at $(git -C "$work" rev-parse HEAD)"
