#! /bin/sh

# Setup dot files.
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

ln -fs "$SCRIPT_DIR"/.bashrc ~/.bashrc
ln -fs "$SCRIPT_DIR"/.bash_aliases ~/.bash_aliases
ln -fs "$SCRIPT_DIR"/.clang-format ~/.clang-format
ln -fs "$SCRIPT_DIR"/.tmux.conf ~/.tmux.conf
ln -fs "$SCRIPT_DIR"/.vim ~/.vim
ln -fs "$SCRIPT_DIR"/i3/config ~/.config/i3/config
ln -fs "$SCRIPT_DIR"/.ideavimr ~/.ideavimrc

rm -rf ~/.atom
ln -fs "$SCRIPT_DIR"/.atom ~/.atom
