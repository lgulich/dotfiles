#!/bin/sh

# Commit the current stashed changes to the passed branch and rebase the current
# branch to include the changes.

set -ex
trap read debug

target_branch=${1:?}
echo "Appending to branch $target_branch."

source_branch="$(git branch --show-current)"
git stash push --staged --message "autostash-staged-for-append"
git stash push --message "autostash-unstaged-for-append"
git checkout $target_branch
git stash apply stash@{1}
git commit
git checkout $source_branch
git rebase $target_branch
git stash apply stash{0}
