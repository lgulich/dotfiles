#!/bin/sh -e

config="$HOME/.config/active_background"

if [ ! -f "$config" ]; then
  echo "color" > "${config}"
fi

if [ "$(cat "${config}")" = "color" ]; then
  echo "black" > "${config}"
  feh --no-fehbg --bg-fill ~/dotfiles/i3/black.jpg
elif [ "$(cat "${config}")" = "black" ]; then
  echo "color" > "${config}"
  feh --no-fehbg --bg-fill ~/dotfiles/i3/wave.jpg
else
  echo "Unknown active background: $(cat "${config}")"
  exit 1
fi
