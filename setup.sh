#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

# Install dependencies
if [ "$OSTYPE" == "linux-gnu" ]; then
  sudo apt-get update && sudo apt-get install -y \
    cmake \
    curl \
    git \
    i3 \
    python3 \
    python3-pip \
    vim \
    tmux \
    zsh
elif [ "$OSTYPE" == "darwin" ]; then
  brew install \
    cmake \
    curl \
    git \
    tmux \
    vim \
    zsh 
fi

# Check that zsh is used.
if [[ ! "$SHELL" =~ .*zsh.* ]]; then
  read -rp "Default shell is not zsh, do you want to change? (Y/n)"
  echo
  if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    chsh -s "$(which zsh)"
    echo "Log out for actions to take change!"
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
echo "source $SCRIPT_DIR/vim/vimrc.vim" > ~/.vimrc
echo "source-file $SCRIPT_DIR/tmux/tmux.conf" > ~/.tmux.conf
echo "source ~/.vimrc" > ~/.ideavimrc

mkdir -p ~/.config/i3
ln -fs "$SCRIPT_DIR"/i3/config ~/.config/i3/config

# Load gnome terminal settings
dconf reset -f /org/gnome/terminal
dconf load /org/gnome/terminal < "$SCRIPT_DIR"/terminal/gnome_terminal_settings.txt

# Install vim plugins.
curl -sL install-node.now.sh/lts | sudo bash # Needed for coc.vim
vim +PlugInstall +qall

