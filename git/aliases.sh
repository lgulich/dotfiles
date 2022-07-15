# shellcheck shell=sh

# Git aliases
alias nah='git reset --hard && git clean -df;'
alias gch='git checkout'
alias gs='git status'
alias ga='git add'
alias gd='git diff --color'
alias gc='git commit'
alias gl='git log'
alias grc='git rebase --continue'
alias grm='git fetch && git rebase origin/master'
alias gca='git commit --amend'
alias gpr='git pull --rebase'
alias gpublish='git_publish_branch'
alias gclean='git_clean_up_branches'
alias applepie='git stash apply'
