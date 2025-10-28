#!/bin/sh

set -e

packages=(
    cmake \
    curl \
    fzf \
    the_silver_searcher \
    wget
)

brew install ${packages} || brew upgrade ${packages}
