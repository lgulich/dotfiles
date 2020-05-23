# shellcheck shell=sh

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
dotfiles="$(dirname "$script_dir")"

# Run tmux if exists.
if command -v tmux>/dev/null; then
	if [ "$DISABLE_TMUX" = "true" ]; then
		echo "DISABLE_TMUX=true"
	else
		[ -z "$TMUX" ] && exec tmux
	fi
else
	echo "tmux not installed, could not autostart tmux"
fi


if [ "$AUTO_UPDATE" = "true" ]; then
  echo "Checking for updates..."
  git -C "$dotfiles" fetch -q > /dev/null 2>&1

  if [ "$(git -C "$dotfiles" rev-list HEAD...origin/master | wc -l)" = 0 ]; then
    echo "Already up to date."
  else
    echo "Updates Detected:"
    git -C "$dotfiles" log ..@{u} --pretty=format:%Cred%aN:%Creset\ %s\ %Cgreen%cd
    echo "Setting up..."
    git -C "$dotfiles" pull -q && git -C "$dotfiles" submodule update --init --recursive
		"$dotfiles"/setup.sh
  fi
fi

. "$script_dir"/zshrc.zsh
