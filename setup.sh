#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

# Install dependencies
sudo apt-get update
sudo apt-get install -y git vim tmux zsh

# Check that zsh is used.
if [[ ! "$SHELL" =~ .*zsh.* ]]; then
  read -p "Default shell is not zsh, do you want to change? (Y/n)"
  echo
  if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    chsh -s "$(which zsh)"
  fi
fi

# Install submodule dependencies.
git -C "$SCRIPT_DIR" submodule init
git -C "$SCRIPT_DIR" submodule update

# Create the dotfiles for the home folder.
printf "source $SCRIPT_DIR/zsh/zshrc_manager.sh" > ~/.zshrc
printf "source $SCRIPT_DIR/vim/vimrc" > ~/.vimrc
printf "source-file $SCRIPT_DIR/tmux/tmux.conf" > ~/.tmux.conf
printf "source ~/.vimrc" > ~/.ideavimrc

ln -fs "$SCRIPT_DIR"/i3/config ~/.config/i3/config

rm -rf ~/.atom
ln -fs "$SCRIPT_DIR"/.atom ~/.atom

# Install vim plugins.
vim +PluginInstall +qall
