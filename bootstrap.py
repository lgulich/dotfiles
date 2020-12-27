#!/usr/bin/env python3.8

import os
import shutil
from pathlib import Path
from datetime import datetime

import yaml


def create_symbolic_links(dotfiles: Path) -> None:
    for child in dotfiles.iterdir():
        if child.is_dir() and (child / 'dotfile_manager.yaml').exists():
            with open(child / 'dotfile_manager.yaml') as file:
                try:
                    symlinks = yaml.load(file,
                                         Loader=yaml.FullLoader)['symlinks']
                except KeyError:
                    continue

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


def create_bin(dotfiles: Path, destination: Path) -> None:
    assert destination.is_dir(), destination
    shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for child in dotfiles.iterdir():
        if child.is_dir() and (child / 'dotfile_manager.yaml').exists():
            with open(child / 'dotfile_manager.yaml') as file:
                try:
                    binaries = yaml.load(file, Loader=yaml.FullLoader)['bin']
                except KeyError:
                    continue

                for binary in binaries:
                    binary_path = child / binary
                    assert binary_path.exists(), binary_path

                    os.symlink(binary_path, destination / binary)
                    print(f'Created symlink from {binary_path} to '
                          f'{destination / binary}.')

    print('Successfully installed symlinks to all binaries.')


def create_sources(dotfiles: Path, destination: Path) -> None:
    destination.unlink(missing_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with open(destination, 'a') as output:
        output.write(f'# Autogenerated on {datetime.now()}.\n')
        output.write(f'# shellcheck shell=zsh\n\n')
        for child in dotfiles.iterdir():
            if child.is_dir() and (child / 'dotfile_manager.yaml').exists():
                with open(child / 'dotfile_manager.yaml') as file:
                    try:
                        source_files = yaml.load(
                            file, Loader=yaml.FullLoader)['source']
                    except KeyError:
                        continue

                    for source_file in source_files:
                        source_path = child / source_file
                        assert source_path.exists(), source_path

                        output.write(f'source {source_path}\n')

                        print(f'Added {source_path} to sourcing script.')

    print(f'Successfully created sourcing file at {destination}.')


def main():
    dotfiles = Path(os.environ['DOTFILES'])
    create_symbolic_links(dotfiles)
    create_bin(dotfiles, dotfiles / 'generated/bin/')
    create_sources(dotfiles, dotfiles / 'generated/sources.zsh')


if __name__ == '__main__':
    main()
