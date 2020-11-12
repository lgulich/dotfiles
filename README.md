# dotfiles

Dotfiles for zsh, vim, tmux and more.

## Installation

Clone this repo and set set the dotfiles environment variable to the path where it is cloned:
```sh
git clone https://github.com/lgulich/dotfiles.git
export DOTFILES=~/dotfiles
```

Depending on your OS run the corresponding command to install all applications:
```sh
./install_darwin.sh # For macOS.
./install_ubuntu.sh # For macOS.
```

Run the following to create the symlinks for all dotfiles.
```sh
./bootstrap.py
```
