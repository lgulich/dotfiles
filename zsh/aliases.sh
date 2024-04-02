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

# Vim
alias vim='nvim'

# Kubernetes
alias kc='kubectl'

# General linux
alias untar='tar -xf'

# Osmo alias
osmo() {
    local args=()
    for arg in "$@"; do
        if [[ "$arg" == "wf" ]]; then
            args+=("workflow")
        elif [[ "$arg" == "ds" ]]; then
            args+=("dataset")
        elif [[ "$arg" == "ls" ]]; then
            args+=("list")
        elif [[ "$arg" == "q" ]]; then
            args+=("query")
        elif [[ "$arg" == "json" ]]; then
            args+=("--format-type=json")
        elif [[ "$arg" == "last" ]]; then
            output="$(command osmo workflow list --count=1 --format-type=json)"
            wf_name="$(echo "$output" | jq -r '.workflows[0].name')"
            args+=("${wf_name}")
        else
            args+=("${arg}")
        fi
    done
    echo "Running command 'osmo ${args[@]}'."
    command osmo "${args[@]}"
}
