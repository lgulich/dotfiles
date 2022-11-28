# Dotfiles [![CI](https://github.com/lgulich/dotfiles/actions/workflows/ci.yml/badge.svg)](https://github.com/lgulich/dotfiles/actions/workflows/ci.yml)
My dotfiles. Feel free to inspire yourself and use whatever you like.

This repo uses the [dotfile manager](https://github.com/lgulich/dotfile_manager)
to organize the dotfiles.

## Getting started
Clone this repo and use the install script the first time.
 Make sure you install it first. (Pip installs
executables to `~/.local/bin`, make sure this is part of your $PATH)

When you use this the first time install everything with
```sh
git clone https://github.com/lgulich/dotfiles.git
cd dotfiles
./install.sh
```
This will install the dependencies dependencies, and install and setup the
individual dotfile projects.

If you have previously already installed the the dependencies you can
also use the dotfile manager directly:

To install new dotfile projects use
```sh
dotfile_manager install
```

To setup a dotfile project use
```sh
dotfile_manager setup
```
