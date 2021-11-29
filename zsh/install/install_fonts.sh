#!/bin/sh

set -e

# Install MesloLGS Nerd Font
mkdir -p ~/.fonts
cp "${DOTFILES:?}"/zsh/fonts/* ~/.fonts
