#!/bin/sh

# Create a new branch on the origin and set it up to track the current branch.

set -e

branch="$(git branch --show-current)"
git push --set-upstream origin "$branch"
