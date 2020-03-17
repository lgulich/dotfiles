SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

# Run tmux if exists.
if command -v tmux>/dev/null; then
	if [ "$DISABLE_TMUX" = "true" ]; then
		echo "DISABLE_TMUX=true"
	else
		[ -z $TMUX ] && exec tmux
	fi
else 
	echo "tmux not installed, could not autostart tmux"
fi


echo "Checking for updates..."
git -C "$SCRIPT_DIR" fetch -q &> /dev/null 

if [ $(git -C "$SCRIPT_DIR" rev-list HEAD...origin/master | wc -l) = 0 ]
then
	echo "Already up to date."
else
	echo "Updates Detected:"
	({cd ~/dotfiles} &> /dev/null && git log ..@{u} --pretty=format:%Cred%aN:%Creset\ %s\ %Cgreen%cd)
	echo "Setting up..."
	({cd ~/dotfiles} &> /dev/null && git pull -q && git submodule update --init --recursive)
fi

source "$SCRIPT_DIR"/zshrc.sh
