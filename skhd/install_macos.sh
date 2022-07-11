#!/bin/sh

set -e

brew install koekeishiya/formulae/skhd
brew services start skhd
