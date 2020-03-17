# ROS & Ascento aliases
alias cda='cd ~/catkin_ws/src/ascento'
alias cdc='cd ~/catkin_ws'
alias srccws='source ~/catkin_ws/devel/setup.bash'
alias kg="killall -9 gazebo & killall -9 gzserver  & killall -9 gzclient"
alias setup_ghostrobot='export ROS_MASTER_URI=http://10.42.0.100:11311; export ROS_IP=10.42.0.100'

# Git aliases
alias nah='git reset --hard; git clean -df;'
alias gs='git status'
alias ga='git add'
alias gc='git commit'

# File browsing aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias srcbashrc='source ~/.bashrc'

# Setup Clion for catkin metapackages. Use like so:
# $ update-clion-ws you_metapackage_name
alias update-clion-ws='rm -rf ~/clion_ws/ && python ~/Documents/editors_tools/init_clion.py -c ~/ -n ~/clion_ws -w ~/catkin_ws' 

