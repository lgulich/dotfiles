#!/usr/bin/env python3

# pylint: skip-file

import re
import subprocess
import getopt
import sys
import os

import i3


def find_parent(window_id):
    """
        Find the parent of a given window id
    """
    root_window = i3.get_tree()
    result = [None]

    def finder(n, p=None):
        if result[0] is not None:
            return
        for node in n:
            if node['id'] == window_id:
                result[0] = p
                return
            if len(node['nodes']) != 0:
                finder(node['nodes'], node)

    finder(root_window['nodes'])
    return result[0]


def set_layout():
    """
        Set the layout/split for the currently
        focused window to either vertical or
        horizontal, depending on its width/height
    """
    current_win = i3.filter(nodes=[], focused=True)
    for win in current_win:
        parent = find_parent(win['id'])

        if (parent \
            and 'rect' in parent \
            and parent['layout'] != 'tabbed'
            and parent['layout'] != 'stacked'):
            height = parent['rect']['height']
            width = parent['rect']['width']

            if height > width:
                new_layout = 'vertical'
            else:
                new_layout = 'horizontal'

            i3.split(new_layout)


def print_help():
    usage = f"""Usage: {sys.argv[0]} [-p path/to/pid.file]

    Options:
        -p path/to/pid.file    Saves the PID for this program in the file.

    """
    print(usage)


def main():
    """
        Main function - listen for window focus
        changes and call set_layout when focus
        changes
    """
    opt_list, _ = getopt.getopt(sys.argv[1:], 'hp:')
    pid_file = None
    for opt in opt_list:
        if opt[0] == '-h':
            print_help()
            sys.exit(1)
        if opt[0] == '-p':
            pid_file = opt[1]

    if pid_file:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))

    process = subprocess.Popen(['xprop', '-root', '-spy'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    regex = re.compile(b'^_NET_CLIENT_LIST_STACKING|^_NET_ACTIVE_WINDOW')

    last_line = ''
    while True:
        line = process.stdout.readline()
        if line == b'':  #X is dead
            break
        if line == last_line:
            continue
        if regex.match(line):
            set_layout()
        last_line = line

    process.kill()
    sys.exit()


if __name__ == '__main__':
    main()
