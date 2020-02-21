# ascento aliases
alias cda='cd ~/catkin_ws/src/ascento'
alias cdc='cd ~/catkin_ws'
alias srccws='source ~/catkin_ws/devel/setup.bash'
alias kg="killall -9 gazebo & killall -9 gzserver  & killall -9 gzclient"

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias srcbashrc='source ~/.bashrc'

# Add an "alert" alias for long running commands.  Use like so:
#  $ sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Setup Clion for catkin metapackages. Use like so:
# $ update-clion-ws you_metapackage_name
alias update-clion-ws='rm -rf ~/clion_ws/ && python ~/Documents/editors_tools/init_clion.py -c ~/ -n ~/clion_ws -w ~/catkin_ws' 

alias setup_ghostrobot='export ROS_MASTER_URI=http://10.42.0.100:11311; export ROS_IP=10.42.0.100'
