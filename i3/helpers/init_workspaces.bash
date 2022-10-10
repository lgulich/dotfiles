#!/bin/bash

set -e

declare -A startup_apps
startup_apps['alacritty']='1'
startup_apps['brave']='2'
startup_apps['slack']='10'
startup_apps['prospect-mail']='10'

startup_workspaces=(
  '2'
  '1'
)

# Start the startup apps.
n_expected_open_windows="$(wmctrl -l | wc -l)"
for app in "${!startup_apps[@]}"; do
  workspace="${startup_apps[$app]}"
  i3-msg workspace "${workspace}"
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

