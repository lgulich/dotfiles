#!/bin/bash

# Amend the current staged changes to a specific commit.

set -e

commit="$1"
if [ -z "$commit" ]; then
  # Select commit interactively if no commit was passed.
  commit=$(git_select_commit.sh 12)
fi

# Amend to commit.
echo "Amending to commit $commit."
git commit --fixup=$commit
stash_name="autostash-for-amend-to-$commit"
git stash push --keep-index --include-untracked --message "$stash_name"
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash $commit^
git stash apply
