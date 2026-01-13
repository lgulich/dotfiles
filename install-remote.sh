#!/bin/bash
# Remote installer for dotfiles
# Usage: curl -fsSL https://raw.githubusercontent.com/lgulich/dotfiles/master/install-remote.sh | bash

set -e

DOTFILES_DIR="${DOTFILES_DIR:-$HOME/.dotfiles}"

echo "Installing dotfiles to $DOTFILES_DIR..."

if [ -d "$DOTFILES_DIR" ]; then
  echo "Dotfiles directory already exists at $DOTFILES_DIR"
  echo "Pulling latest changes..."
  git -C "$DOTFILES_DIR" pull
else
  echo "Cloning dotfiles..."
  git clone https://github.com/lgulich/dotfiles.git "$DOTFILES_DIR"
fi

cd "$DOTFILES_DIR"
./install.sh
