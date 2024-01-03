#!/bin/bash

# Create a branch for every commit since master that doesn't have a branch yet.

set -e

commit="$1"
if [ -z "$commit" ]; then
  # Select commit interactively if no commit was passed.
  commit=$(git_select_commit.sh 12)
fi

# Amend to commit.
echo "Amending to commit '$commit'."
git commit --fixup=$commit
# If the git repo is dirty we have to stash it before rebasing.
git diff --quiet || dirty=true
if [ -n "$dirty" ]; then
  echo "Git directory is dirty: stashing changes."
  stash_name="autostash-for-amend-to-$commit"
  git stash push --keep-index --include-untracked --message "$stash_name"
fi
echo "Rebasing the amended commit."
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash $commit^
if [ -n "$dirty" ]; then
  echo "Applying stashed changes."
  git stash apply
fi
