#!/bin/sh

set -ex

brew install koekeishiya/formulae/yabai
sudo yabai --install-sa
brew services start yabai
killall Dock
