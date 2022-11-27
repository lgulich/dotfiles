#!/bin/sh

# Reset a branch to its counterpart on remote "origin".

set -e

git fetch origin
branch="$(git branch --show-current)"
git reset --hard "origin/$branch"
