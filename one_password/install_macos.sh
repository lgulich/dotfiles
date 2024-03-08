#!/bin/sh

set -e

brew install mas
mas install 1569813296  # 1Password for Safari

brew install --cask 1password
brew install 1password-cli

# Verify installation
op --version
