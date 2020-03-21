#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

# Install dependencies
sudo apt-get update
sudo apt-get install -y git vim tmux zsh

# Check that zsh is used.
if [[ ! "$SHELL" =~ .*zsh.* ]]; then
  read -rp "Default shell is not zsh, do you want to change? (Y/n)"
  echo
  if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    chsh -s "$(which zsh)"
  fi
fi

# Install submodule dependencies.
git -C "$SCRIPT_DIR" submodule init
git -C "$SCRIPT_DIR" submodule update

# Install vim-plug.
curl -fLo "$SCRIPT_DIR"/vim/vim_plug/autoload/plug.vim --create-dirs \
  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# Create the dotfiles for the home folder.
echo "source $SCRIPT_DIR/zsh/zshrc_manager.sh" > ~/.zshrc
echo "source $SCRIPT_DIR/vim/vimrc" > ~/.vimrc
echo "source-file $SCRIPT_DIR/tmux/tmux.conf" > ~/.tmux.conf
echo "source ~/.vimrc" > ~/.ideavimrc

ln -fs "$SCRIPT_DIR"/i3/config ~/.config/i3/config

rm -rf ~/.atom
ln -fs "$SCRIPT_DIR"/.atom ~/.atom

# Install vim plugins.
vim +PluginInstall +qall
