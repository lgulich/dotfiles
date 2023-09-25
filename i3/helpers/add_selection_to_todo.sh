#!/bin/sh

set -e

TODO_FILE=~/tasks.todo

clipboard_content=`xclip -o`
zenity --question --width 300 --text "Add\n'$clipboard_content'\nto TODO list?"
echo "- [] $clipboard_content" >> $TODO_FILE
notify-send "Added '$clipboard_content' to TODO list."

