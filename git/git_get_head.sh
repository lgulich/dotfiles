#!/bin/sh

# Prints the name of the current head: either a branch name or a commit hash.

set -e

status="$(git status)"
regex="^(On branch |HEAD detached at )(.*)$"
[[ $status =~ $regex ]]; echo "${BASH_REMATCH[1]}"
