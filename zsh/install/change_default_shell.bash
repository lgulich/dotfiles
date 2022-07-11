#!/bin/bash

set -e

# Check that zsh is used.
if [[ ! "${SHELL}" =~ .*zsh.* ]]; then
  sudo chsh -s "$(which zsh)"
  echo "Changed shell to zsh. Log out for actions to take change!"
fi
