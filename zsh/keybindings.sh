# Prepend sudo to command
zle -N add_sudo
bindkey "^s" add_sudo

# Edit last command in vim
zle -N edit_last_command
bindkey "^v" edit_last_command

# Go to $HOME
zle -N go_to_home
bindkey "^h" go_to_home

# Go up one folder
zle -N go_up_one_folder
bindkey "^k" go_up_one_folder

# Go to git root
zle -N go_to_git_root
bindkey "^g" go_to_git_root

# Fuzzy search history
# start typing + [Up-Arrow] - fuzzy find history forward
if [[ "${terminfo[kcuu1]}" != "" ]]; then
	autoload -U up-line-or-beginning-search
	zle -N up-line-or-beginning-search
	bindkey "${terminfo[kcuu1]}" up-line-or-beginning-search
fi
# start typing + [Down-Arrow] - fuzzy find history backward
if [[ "${terminfo[kcud1]}" != "" ]]; then
	autoload -U down-line-or-beginning-search
	zle -N down-line-or-beginning-search
	bindkey "${terminfo[kcud1]}" down-line-or-beginning-search
fi
