#!/bin/sh

set -e

brew install jq

brew install koekeishiya/formulae/yabai
sudo yabai --install-sa
brew services start yabai
killall Dock
