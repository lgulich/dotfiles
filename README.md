# Dotfiles
My dotfiles. Feel free to inspire yourself and use whatever you like.

## Installation
This repo uses the [dotfile manager](https://github.com/lgulich/dotfile_manager)
to organize the dotfiles. Make sure you install it first.
```sh
pip install dotfile-manager
```

Clone this repo and then use the dotfile manager to install and set everything
up.
```sh
git clone https://github.com/lgulich/dotfiles.git
export DOTFILES="$(pwd)"/dotfiles

dotfile_manager install
dotfile_manager setup
```
