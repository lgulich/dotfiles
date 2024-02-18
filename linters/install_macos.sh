#!/bin/bash

set -e

brew install clang-format

python3 -m pip install yapf pylint pre-commit
