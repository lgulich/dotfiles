#!/bin/bash -ex

declare -A startup_apps
startup_apps['1']='alacritty'
startup_apps['2']='brave-browser-beta'
startup_apps['10']='franz'

startup_workspaces=(
  '2'
  '1'
)

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

for workspace in "${startup_workspaces[@]}"; do
  i3-msg workspace "${workspace}"
done

