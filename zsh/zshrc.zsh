# shellcheck shell=zsh

# Run tmux if exists.
if command -v tmux>/dev/null; then
  [ -z "$TMUX" ] && exec tmux
else
  echo "tmux not installed, could not autostart tmux."
fi

# Load .profile
[ -f ~/.profile ] && source ~/.profile

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi


# Oh my zsh configuration
export ZSH="${HOME}/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(
  vi-mode
  git
  zsh-autosuggestions
)
source "${ZSH}"/oh-my-zsh.sh

# Often used directories. 
export DOTFILES=~/dotfiles
export ARC_CORE_PATH=~/arc_core
export ARC_WS_PATH=~/arc_ws
# Default UNIX env variables:
export PATH="/usr/lib/ccache:${PATH}" # ccache for faster builds.
export PATH="${DOTFILES}/generated/bin:${PATH}"
export CXX=/usr/bin/g++-9
export VISUAL=vim
export EDITOR=vim
# SSL
export OPENSSL_ROOT_DIR=/usr/local/opt/openssl@1.1

source "${DOTFILES}"/generated/sources.zsh

# Load fzf fuzzyfinder.
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Load ROS.
[ -f /opt/ros/melodic/setup.zsh ] && source /opt/ros/melodic/setup.zsh

