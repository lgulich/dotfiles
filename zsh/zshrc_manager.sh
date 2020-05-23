# shellcheck shell=sh

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"

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

. "$script_dir"/zshrc.zsh
