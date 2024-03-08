#!/bin/sh

set -e

yabai --stop-service || true
brew install koekeishiya/formulae/yabai
yabai --start-service
