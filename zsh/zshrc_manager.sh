SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
DOTFILES="$(dirname "$SCRIPT_DIR")"

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


echo "Checking for updates..."
git -C "$DOTFILES" fetch -q &> /dev/null

if [ "$(git -C "$DOTFILES" rev-list HEAD...origin/master | wc -l)" = 0 ]
then
	echo "Already up to date."
else
	echo "Updates Detected:"
	git -C "$DOTFILES" log ..@{u} --pretty=format:%Cred%aN:%Creset\ %s\ %Cgreen%cd
	echo "Setting up..."
	git -C "$DOTFILES" pull -q && git -C "$DOTFILES" submodule update --init --recursive
fi

source "$SCRIPT_DIR"/zshrc.sh
