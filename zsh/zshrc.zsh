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
export DOTFILES=~/Code/dotfiles

# Default UNIX env variables:
export PATH="/usr/lib/ccache:${PATH}" # ccache for faster builds.
export PATH="${DOTFILES:?}/generated/bin:${PATH}"
export VISUAL=vim
export EDITOR=vim
export BROWSER=brave

# SSL
export OPENSSL_ROOT_DIR=/usr/local/opt/openssl@1.1

# Source files generated by dotfiles
source "${DOTFILES:?}"/generated/sources.sh

# Load fzf fuzzyfinder.
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
export FZF_DEFAULT_COMMAND='fd --type f'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"

# Load ROS.
[ -f /opt/ros/foxy/setup.zsh ] && source /opt/ros/foxy/setup.zsh

# Bazel autocomplete, caches bazel's options:
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path ~/.zsh/cache

# Load OSMO
export OSMO_PATH="/home/lgulich/Code/osmo"
export PATH=$PATH:$OSMO_PATH
export ISAAC_DEV_BAZEL=bazel
