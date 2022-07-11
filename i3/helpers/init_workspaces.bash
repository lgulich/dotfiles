#!/bin/bash

set -e

declare -A startup_apps
startup_apps['1']='alacritty'
startup_apps['2']='brave-browser'
startup_apps['10']='slack'
startup_apps['10']='prospect-mail'

startup_workspaces=(
  '2'
  '1'
)

# Start the startup apps.
n_expected_open_windows="$(wmctrl -l | wc -l)"
for workspace in "${!startup_apps[@]}"; do
  i3-msg workspace "${workspace}"
  app="${startup_apps[$workspace]}"
  "${app}" &
  ((++n_expected_windows))

  n_opened_windows="$(wmctrl -l | wc -l)"
  while [ "$n_opened_windows" -lt "$n_expected_open_windows" ]; do
    sleep 0
  done
done

# Go to the startup workspaces.
for workspace in "${startup_workspaces[@]}"; do
  i3-msg workspace "${workspace}"
done

