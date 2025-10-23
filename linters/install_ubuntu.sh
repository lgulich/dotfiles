#!/bin/bash

set -e

sudo apt-get install -y clang-format

python3 -m pip install --break-system-packages yapf pylint pre-commit
