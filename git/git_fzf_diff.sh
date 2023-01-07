#!/bin/sh

# Show the git diff in an fzf preview window.

preview="git diff $@ --color=always -- {-1}"
git diff $@ --name-only | fzf -m --ansi --preview $preview
