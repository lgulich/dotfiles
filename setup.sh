#!/bin/bash

set -e

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"

# Install dependencies
if [[ "$OSTYPE" =~ "linux-gnu" ]]; then
  sudo apt-get update
  sudo apt-get install -y \
    cmake \
    compton \
    curl \
    feh \
    git \
    i3 \
    nodejs \
    python3 \
    python3-pip \
    tmux \
    vim \
    zsh
elif [[ "$OSTYPE" =~ "darwin" ]]; then
  brew install koekeishiya/formulae/yabai
  sudo yabai --install-sa
  brew services start yabai
  killall Dock

  brew install koekeishiya/formulae/skhd
  brew services start skhd

  brew install \
    cmake \
    curl \
    git \
    nodejs \
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
echo "source $script_dir/zsh/zshrc_manager.sh" > "$HOME"/.zshrc
echo "source $script_dir/vim/vimrc.vim" > "$HOME"/.vimrc
echo "source-file $script_dir/tmux/tmux.conf" > "$HOME"/.tmux.conf
echo "source $HOME/.vimrc" > "$HOME"/.ideavimrc

# Install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended --keep-zshrc || true

# Install oh-my-zsh plugins
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"/themes/powerlevel10k || true
git clone https://github.com/zsh-users/zsh-autosuggestions "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"/plugins/zsh-autosuggestions || true



if [[ "$OSTYPE" =~ "linux-gnu" ]]; then
  # i3 does not allow to source config files, thus we have to symlink it.
  mkdir -p "$HOME"/.config/i3
  ln -fs "$script_dir"/i3/config "$HOME"/.config/i3/config

  ln -fs "$script_dir"/compton/compton.conf "$HOME"/.config/compton.conf

  # Install MesloLGS Nerd Font
  mkdir -p ~/.fonts
  cp "$script_dir"/terminal/fonts/* ~/.fonts

  # Load gnome terminal settings
  dconf reset -f /org/gnome/terminal/
  dconf load /org/gnome/terminal/ < "$script_dir"/terminal/gnome_terminal_settings.txt
elif [[ "$OSTYPE" =~ "darwin" ]]; then
  ln -fs "$script_dir"/yabai/yabairc "$HOME"/.config/yabairc
  ln -fs "$script_dir"/skhd/skhdrc "$HOME"/.config/skhdrc
fi

# Same goes for alacrittys yaml config file.
mkdir -p "$HOME"/.config/alacritty
ln -fs "$script_dir"/alacritty/alacritty.yml "$HOME"/.config/alacritty/alacritty.yml

# Install plugin manager vim-plug.
curl -fLo "$script_dir"/vim/vim_plug/autoload/plug.vim --create-dirs \
  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# Install vim plugins.
vim +PlugInstall +qall
