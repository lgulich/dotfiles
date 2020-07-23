#!/bin/bash -ex

startup_apps=(
  'alacritty'
  'brave-browser-beta'
  'franz'
)

# startup_apps=(
#   ['1']=('alacritty')
#   ['2']=('brave-browser-beta')
#   ['3']=('franz')
# )

# Which workspace to assign your wanted App :
workspaces=(
  '1'
  '2'
  '10'
)

startup_workspaces=(
  '1'
  '2'
)

n_opened_windows=0

for i in ${!startup_apps[*]}; do
  # Wait before start other programs.
  while [ "$n_opened_windows" -lt "$i" ]; do
    # Update number of actual opened windows.
    n_opened_windows=$(wmctrl -l | wc -l)
  done

  # Move to desired workspace and open app.
  i3-msg workspace ${workspaces[$i]}
  ${startup_apps[$i]} &
done

for i in ${!startup_workspaces[*]}; do
  i3-msg workspace ${startup_workspaces[$i]}
done

