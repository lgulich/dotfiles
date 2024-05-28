# shellcheck shell=zsh

function add_sudo() {
  BUFFER="sudo "$BUFFER
  zle end-of-line
}
zle -N add_sudo
bindkey "^s" add_sudo

function edit_last_command() {
  BUFFER="fc"
  zle accept-line
}
zle -N edit_last_command
bindkey "^v" edit_last_command

function go_up_one_folder() {
  BUFFER="cd .."
  zle accept-line
}
zle -N go_up_one_folder
bindkey "^k" go_up_one_folder

function go_to_home() {
  BUFFER="cd ~/"
  zle accept-line
}
zle -N go_to_home
bindkey "^h" go_to_home

function go_to_git_root() {
  BUFFER="git_go_to_repo_root"
  zle accept-line
}
zle -N go_to_git_root
bindkey "^g" go_to_git_root

# Fuzzy find history backward: start typing + [Up-Arrow].
if [[ "${terminfo[kcuu1]}" != "" ]]; then
	autoload -U up-line-or-beginning-search
	zle -N up-line-or-beginning-search
	bindkey "${terminfo[kcuu1]}" up-line-or-beginning-search
fi

# Fuzzy find history forward: start typing + [Down-Arrow].
if [[ "${terminfo[kcud1]}" != "" ]]; then
	autoload -U down-line-or-beginning-search
	zle -N down-line-or-beginning-search
	bindkey "${terminfo[kcud1]}" down-line-or-beginning-search
fi

# Keymap to exit vi-insert-mode.
bindkey "jk" vi-cmd-mode

# Partially complete suggestion by zsh-autosuggestions.
bindkey '^ ' forward-word

# Feed current buffer to sgpt.
feed_buffer_to_sgpt() {
  if [[ -n "$BUFFER" ]]; then
      _sgpt_prev_cmd=$BUFFER
      BUFFER+="⌛"
      zle -I && zle redisplay
      BUFFER=$(sgpt --shell <<< "$_sgpt_prev_cmd" --no-interaction)
      zle end-of-line
  fi
}
zle -N feed_buffer_to_sgpt
bindkey ^o feed_buffer_to_sgpt
