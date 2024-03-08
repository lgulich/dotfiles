#!/bin/sh

set -e

skhd --stop-services || true
brew install koekeishiya/formulae/skhd
skhd --start-service
