#!/bin/sh

set -e

# Load gnome terminal settings.
dconf reset -f /org/gnome/terminal/
dconf load /org/gnome/terminal/ < "${DOTFILES:?}"/gnome_terminal/settings.txt
