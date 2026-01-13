#!/bin/sh

set -e

# Try to add PPA and install alacritty (may fail in restricted environments)
if sudo python3.12 /usr/bin/add-apt-repository ppa:aslatter/ppa -y 2>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y alacritty
else
    echo "Warning: Could not add PPA (network issue?), trying default repositories..."
    # Try installing from default repos (may be older version or not available)
    if ! sudo apt-get install -y alacritty 2>/dev/null; then
        echo "Warning: Could not install alacritty from default repositories either. Skipping."
        exit 0
    fi
fi
