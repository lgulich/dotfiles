#!/bin/sh

set -ex

brew install koekeishiya/formulae/skhd
brew services start skhd
