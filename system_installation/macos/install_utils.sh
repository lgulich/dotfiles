#!/bin/sh

set -e

packages=(
    cmake \
    curl \
    wget \
    the_silver_searcher \
)

brew install ${packages} || brew upgrade ${packages}