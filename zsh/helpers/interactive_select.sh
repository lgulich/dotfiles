#!/bin/bash

set -e

selection_options=( "$@" )

if ! command -v fzf &> /dev/null; then
    echo "Error: fzf is not installed. Please install it and try again."
    exit 1
fi

# Use fzf for interactive selection of a name
selected_option=$(printf "%s\n" "${selection_options[@]}" | fzf --height=~50% --prompt="Select an option: ")

# Check if a name was selected
if [ -z "${selected_option}" ]; then
    echo "No option selected."
    exit 1
fi

# Output the selected name
echo "${selected_option}"
