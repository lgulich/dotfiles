#!/bin/bash

# Use this script to merge all .mcap files in a directory.

# Set the target directory from CLI argument or use the current directory
target_dir="${1:-.}"

# Find all .mcap files larger than 1 byte in the target directory
mcap_files=($(find "$target_dir" -maxdepth 1 -type f -name "*.mcap" -size +1c | sort -V))

# Check if there are files to merge
if [ ${#mcap_files[@]} -eq 0 ]; then
    echo "No valid MCAP files found in $target_dir."
    exit 1
fi

# Run the merge command
mcap merge -o "$target_dir/final.mcap" --allow-duplicate-metadata "${mcap_files[@]}"

echo "Merged ${#mcap_files[@]} MCAP files into $target_dir/final.mcap"
