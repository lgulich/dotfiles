#!/bin/bash

set -ex

brew install zsh || brew upgrade zsh

# Check that zsh is used.
if [[ ! "$SHELL" =~ .*zsh.* ]]; then
  read -rp "Default shell is not zsh, do you want to change? (Y/n)"
  echo
  if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    sudo chsh -s "$(which zsh)"
    echo "Log out for actions to take change!"
  fi
fi

"${DOTFILES}"/zsh/install/install_oh_my_zsh.sh
"${DOTFILES}"/zsh/install/install_fonts.sh
