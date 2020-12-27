# Dotfiles
A dotfile manager to easily reuse configurations between linux and macOS. 
Configurations for zsh, vim, tmux and more.

Disclaimer: Feel free to clone / fork / do what you like with this repo. But
please know that I give no guarantee for the correctness and also take the
liberty to push / merge / force-push to this repo as I like.

## Installation
Clone this repo and set set the dotfiles environment variable to the path where 
it is cloned:
```sh
git clone https://github.com/lgulich/dotfiles.git
export DOTFILES="$(pwd)"/dotfiles
```

Depending on your OS run the corresponding command to install all applications:
```sh
./install.sh --darwin # For macOS.
./install.sh --ubuntu # For ubuntu.
```

To setup the dotfiles run the following command. This will setup symbolic of the
config files, symlink the binaries and create a script to source everything.
```sh
./bootstrap.py
```

## Usage
The dotfiles are organised by topic, where each topic has its own top-level 
folder. A topic may contain a file `dotfile_manager.yaml` which configures the
dotfile manager. It is setup as follows:
```yaml
symlink:
  zshrc.zsh: ~/.zshrc

bin:
  - do_something.sh

source:
  - aliases.sh
  - helpers.sh
```
The entries of `symlink` configures where the files will be symlinked to, the
key is the path of the file inside the topic folder, the value is the global
path where the file will be symlinked to.

The entries of `bin` will be symlinked to `${DOTFILES}/generated/bin/`. Add this
folder to your path to easily access these binaries.

The entries of `source` will be added to a script in
`${DOTFILES}/generated/sources.zsh`, such that you only have to source this file
instead of sourcing all files individually.
