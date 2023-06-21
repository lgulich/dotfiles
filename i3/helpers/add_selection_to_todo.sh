#!/bin/sh

set -e

TODO_FILE=~/tasks.todo

clipboard_content=`xclip -o`
echo "- [] $clipboard_content" >> $TODO_FILE
notify-send "Added '$clipboard_content' to TODO list."

