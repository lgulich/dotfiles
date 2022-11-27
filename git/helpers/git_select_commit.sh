#!/bin/bash

set -e

DEFAULT_HISTORY_SIZE=9
HISTORY_SIZE=${1:-$DEFAULT_HISTORY_SIZE}

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

echo "${HASHES[$CHOICE]}."
