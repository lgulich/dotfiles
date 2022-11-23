#!/bin/bash

set -e

# Select the commit interactively.
HISTORY_SIZE=${HISTORY_SIZE:-12}

IFS=$'\n'
HASHES=($(git log --pretty=format:"%h" -n $HISTORY_SIZE))
TITLES=($(git log --pretty=format:"%s" -n $HISTORY_SIZE))

PS3="Select a commit: "
select TITLE in ${TITLES[@]}; do
  CHOICE=$((${REPLY}-1))
  if (($CHOICE>=$HISTORY_SIZE)); then
    echo "Error: Please select a commit in the displayed range."
    continue
  fi
  break
done

COMMIT="${HASHES[$CHOICE]}"
echo "You selected commit \"$COMMIT - $TITLE\"."

# Amend to commit.
echo "Amending to commit $COMMIT."
git commit --fixup=$COMMIT
STASH_NAME="autostash-for-amend-to-$COMMIT"
git stash push --keep-index --include-untracked --message "$STASH_NAME"
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash $COMMIT^
git stash apply
