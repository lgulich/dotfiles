#!/bin/sh

set -e

brew install --cask alacritty

# Allow opening this app because it's from an uncertified developer.
xattr -dr com.apple.quarantine "/Applications/Alacritty.app"
