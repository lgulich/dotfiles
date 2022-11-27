#!/bin/sh

git_get_head() {
  local status="$(git status)"
  local regex="^(On branch |HEAD detached at )(.*)$"
  [[ $status =~ $regex ]]; echo "${BASH_REMATCH[1]}"
}

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
