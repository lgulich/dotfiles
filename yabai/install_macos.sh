#!/bin/sh

set -e

yabai --stop-service || true
brew install koekeishiya/formulae/yabai

# Allow running `sudo yabai --load-sa` without sudo password.
echo "$(whoami) ALL=(root) NOPASSWD: sha256:$(shasum -a 256 $(which yabai) | cut -d " " -f 1) $(which yabai) --load-sa" | sudo tee /private/etc/sudoers.d/yabai

yabai --start-service
