# shellcheck shell=sh

alias dot='${DOTFILES:?}'
alias doc='${~/Documents/}'

# General aliases
alias edf='edit_dotfile.zsh'
alias todo='vim ~/tasks.todo'

# File browsing aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias cd='cd_and_ls'

# Vim
alias vim='nvim'

# Kubernetes
alias kc='kubectl'

# General linux
alias untar='tar -xf'

alias osmo='osmo.sh'
alias osmo_pf='osmo.sh wf pf select train --port 6006,8080'
