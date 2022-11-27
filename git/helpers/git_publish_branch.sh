#!/bin/sh

set -e

git_publish_branch() {
  branch="$(git branch --show-current)"
  git push --set-upstream origin "$branch"
}
