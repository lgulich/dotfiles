#!/usr/bin/env python3

import os
from pathlib import Path

import yaml


def create_symbolic_links():
    dotfiles = Path(os.environ['DOTFILES'])
    for child in dotfiles.iterdir():
        if child.is_dir() and (child/'symlink.yaml').exists():
            with open(child/'symlink.yaml') as file:
                symlinks = yaml.load(file, Loader=yaml.FullLoader)
                for source, destination in symlinks.items():
                    source_path = child / source
                    assert source_path.exists(), source_path

                    destination_path = Path(destination).expanduser()
                    destination_path.parent.mkdir(parents=True, exist_ok=True)
                    destination_path.unlink(missing_ok=True)

                    os.symlink(source_path, destination_path)
                    print(f'Created symlink from {source_path} to '
                            f'{destination_path}.')

    print('Successfully installed symlinks to all dotfiles.')


if __name__ == '__main__':
    create_symbolic_links()



