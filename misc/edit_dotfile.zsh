#!/bin/zsh 

set -e

# Add new config options here, path is from root of dotfiles repo.
declare -A config_paths
config_paths[alacritty]="alacritty/alacritty.yml"
config_paths[compton]="compton/compton.conf"
config_paths[i3]="i3/config"
config_paths[tmux]="tmux/tmux.conf"
config_paths[vim]="vim/vanillavimrc.vim"
config_paths[vim-plugins]="vim/vimrc.vim"
config_paths[vim-vanilla]="vim/vanillavimrc.vim"
config_paths[zsh]="zsh/zshrc.zsh"

if [ -n "$1" ]; then
  choice="$1"
else
  # We convert the array to a newline separated list which can be read by dmenu.
  options_string=""
  for key in "${(@k)config_paths}"; do
    options_string="${options_string}${key}\n"
  done

  # Get choice from dmenu.
  choice=$(echo -e "${options_string}" | dmenu)
fi

[ "$?" = 0 ] && "${EDITOR:?}" "${DOTFILES:?}/${config_paths[$choice]}"

