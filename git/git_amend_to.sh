#!/bin/bash

set -e

# Select the commit interactively.
HISTORY_SIZE=${HISTORY_SIZE:-9}

IFS=$'\n'
HASHES=($(git log --pretty=format:"%h" -n $HISTORY_SIZE))
TITLES=($(git log --pretty=format:"%s" -n $HISTORY_SIZE))

echo "Select a commit:"
for ((i=0; $i<$HISTORY_SIZE; i++)); do
  echo "  $((i+1)). ${HASHES[i]} ${TITLES[i]}"
done

read -p "Enter commit [1-$HISTORY_SIZE] > "
CHOICE=$((${REPLY}-1))

if (($CHOICE>=$HISTORY_SIZE)); then
  echo "Error: Please select a commit in the displayed range."
  exit 1
fi

# Amend to commit.
COMMIT="${HASHES[$CHOICE]}"
echo "Amending to commit $COMMIT"
git commit --fixup=$COMMIT
STASH_NAME="autostash-for-amend-to-$COMMIT"
git stash push --keep-index --include-untracked --message "$STASH_NAME"
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash $COMMIT^
git stash apply
