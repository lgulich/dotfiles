#!/bin/sh

set -e

git fetch origin
branch="$(git branch --show-current)"
git reset --hard "origin/$branch"
