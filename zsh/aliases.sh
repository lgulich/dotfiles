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

# Isaac development
alias cdi='cd ~/Code/isaac/'
alias cdis='cd ~/Code/isaac/sdk'
alias cdg='cd ~/Code/gxf/'
alias cdws='cd ~/workspaces/isaac_ros-dev'
alias cdwss='cd ~/workspaces/isaac_ros-dev/src'

# Vim
alias vim='nvim'

# Kubernetes
alias kc='kubectl'
