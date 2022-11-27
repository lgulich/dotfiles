#!/bin/bash

# Use an interactive cli editor to select a commit.

set -e

# Select the commit interactively.
history_size=${history_size:-12}

IFS=$'\n'  # Needed to make every new line a new entry in the bash array
hashes=($(git log --pretty=format:"%h" -n $history_size))
titles=($(git log --pretty=format:"%s" -n $history_size))

COLUMNS=20  # Force select to use only a single column
PS3="Select a commit: "
select title in ${titles[@]}; do
  choice=$((${REPLY}-1))
  if (($choice>=$history_size)); then
    echo "Error: Please select a commit in the displayed range."
    exit 1
  fi
  break
done

commit="${hashes[$choice]}"
echo "You selected commit '$title' - '$commit'." >&2
echo "$commit"
