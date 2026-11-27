#!/bin/sh
# Replace the "hermes" branch with the tree in <dir> (built by build_dist.py --hermes) and push it.
#
#   sh scripts/publish-hermes-branch.sh dist/hermes v0.1.0
#
# The commit is built inside the current repository with a throwaway index and pushed through
# the repository's own remote, so whatever credentials that remote already uses (an SSH key
# locally, the checkout token in GitHub Actions) apply. Nothing in the working tree changes.
set -eu

tree=$(cd "$1" && pwd)
label=${2:-unreleased}
remote=${SAGES_REMOTE:-origin}
git_dir=$(git rev-parse --absolute-git-dir)
index=$(mktemp)
rm -f "$index"
trap 'rm -f "$index"' EXIT

export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-NTP-996}"
export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-31298991+NTP-996@users.noreply.github.com}"
export GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-$GIT_AUTHOR_NAME}"
export GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-$GIT_AUTHOR_EMAIL}"

GIT_INDEX_FILE="$index" git --git-dir="$git_dir" --work-tree="$tree" -C "$tree" add -A -f .
tree_id=$(GIT_INDEX_FILE="$index" git --git-dir="$git_dir" write-tree)
commit=$(git --git-dir="$git_dir" commit-tree "$tree_id" -m "build: Hermes Agent tree for $label")
git --git-dir="$git_dir" push -q --force "$remote" "$commit:refs/heads/hermes"
echo "hermes branch published at $commit"
