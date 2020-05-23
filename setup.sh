#!/bin/bash -e

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"

# Install dependencies
if [ "$OSTYPE" == "linux-gnu" ]; then
  sudo apt-get update && sudo apt-get install -y \
    cmake \
    curl \
    git \
    i3 \
    nodejs \
    python3 \
    python3-pip \
    vim \
    tmux \
    zsh
elif [ "$OSTYPE" == "darwin" ]; then
  brew install \
    cmake \
    curl \
    git \
    nodejs \
    tmux \
    vim \
    zsh
fi

# Check that zsh is used.
if [[ ! "$SHELL" =~ .*zsh.* ]]; then
  read -rp "Default shell is not zsh, do you want to change? (Y/n)"
  echo
  if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    chsh -s "$(which zsh)"
    echo "Log out for actions to take change!"
  fi
fi

# Install submodule dependencies.
git -C "$script_dir" submodule init
git -C "$script_dir" submodule update

# Create the dotfiles for the home folder.
echo "source $script_dir/zsh/zshrc_manager.sh" > ~/.zshrc
echo "source $script_dir/vim/vimrc.vim" > ~/.vimrc
echo "source-file $script_dir/tmux/tmux.conf" > ~/.tmux.conf
echo "source ~/.vimrc" > ~/.ideavimrc

# Install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended --keep-zshrc

# Install oh-my-zsh plugins
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}"/themes/powerlevel10k
git clone https://github.com/zsh-users/zsh-autosuggestions "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}"/plugins/zsh-autosuggestions

# i3 does not allow to source config files, thus we have to symlink it.
mkdir -p ~/.config/i3
ln -fs "$script_dir"/i3/config ~/.config/i3/config

# Load gnome terminal settings
dconf reset -f /org/gnome/terminal/
dconf load /org/gnome/terminal/ < "$script_dir"/terminal/gnome_terminal_settings.txt

# Install plugin manager vim-plug.
curl -fLo "$script_dir"/vim/vim_plug/autoload/plug.vim --create-dirs \
  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# Install vim plugins.
vim +PlugInstall +qall
