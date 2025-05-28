#!/usr/bin/env python3
"""Use this script to generate a graph visulization of a yaml file with nested dicts."""

import argparse
import pathlib

import yaml
from anytree import Node
from anytree.exporter import DotExporter


# Step 2: Recursive tree builder
def build_tree(data: dict, parent_node: Node):
    for node_name, node_data in (data or {}).items():
        node = Node(node_name, parent=parent_node)
        build_tree(node_data['deps'], node)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_file', type=pathlib.Path)
    parser.add_argument('output', type=pathlib.Path)
    args = parser.parse_args()

    data = yaml.safe_load(args.yaml_file.read_text())

    tree = Node('root')
    build_tree(data, tree)

    DotExporter(tree).to_picture(args.output)


if __name__ == '__main__':
    main()
