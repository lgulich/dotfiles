#!/bin/bash

set -e

sudo apt-get install -y zsh

# Check that zsh is used.
if [[ ! "$SHELL" =~ .*zsh.* ]]; then
  read -rp "Default shell is not zsh, do you want to change? (Y/n)"
  echo
  if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    chsh -s "$(which zsh)"
    echo "Log out for actions to take change!"
  fi
fi

SCRIPT_PATH=$(dirname $(realpath -s $0))
"${SCRIPT_PATH}"/install/install_oh_my_zsh.sh
"${SCRIPT_PATH}"/install/install_fonts.sh
