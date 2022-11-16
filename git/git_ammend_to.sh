#!/bin/sh

set -e

COMMIT=${1:?No argument passed, commit is needed as first argument}
echo "Ammending to commit $COMMIT"
git commit --fixup=$COMMIT
STASH_NAME="autostash-for-amend-to-$COMMIT"
git stash push --keep-index --include-untracked --message "$STASH_NAME"
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash $COMMIT^
git stash apply
