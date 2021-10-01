# Dotfiles
My dotfiles.

## Installation
This repo uses the [dotfile manager](https://github.com/lgulich/dotfile_manager).

Clone this repo and then use the dotfile manager to install and set everything
up.
```sh
git clone https://github.com/lgulich/dotfiles.git
export DOTFILES="$(pwd)"/dotfiles

pip install dotfile-manager
dotfile_manager install
dotfile_manager setup
```
