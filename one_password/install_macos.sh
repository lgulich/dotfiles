#!/bin/sh

set -e

brew install --cask 1password/tap/1password-cli

op --version  # To verify installation
