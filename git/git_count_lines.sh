#!/bin/sh

# Counts the contributions of an author in a git repository.

set -e

author="${1:?}"

git log --author="$author" --pretty=tformat: --numstat | awk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf \"added lines: %s, removed lines: %s, total lines: %s\\n\", add, subs, loc }'
