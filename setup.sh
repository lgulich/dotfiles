#!/bin/sh

# Setup dot files.
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

git -C "$SCRIPT_DIR" submodule init
git -C "$SCRIPT_DIR" submodule update

printf "source $SCRIPT_DIR/zsh/zshrc_manager.sh" > ~/.zshrc
printf "source $SCRIPT_DIR/vim/vimrc" > ~/.vimrc
printf "source-file $SCRIPT_DIR/tmux/tmux.conf" > ~/.tmux.conf
printf "source ~/.vimrc" > ~/.ideavimrc

ln -fs "$SCRIPT_DIR"/i3/config ~/.config/i3/config

rm -rf ~/.atom
ln -fs "$SCRIPT_DIR"/.atom ~/.atom

vim +PluginInstall +qall
