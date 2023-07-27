#!/bin/bash

# Use this script to run multiple targets matching a regex.
# Usage bazel_regex [build|test|run] pattern

set -e

# Change to bazel workspace root dir if this script is run from bazel
cd "${BUILD_WORKING_DIRECTORY:-.}"

mode=${1:?}
pattern=${2:?}
shift 2

bazel=auto
workspace='.'
search_path='//...'

# get command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    -b|--bazel)
      bazel="$2"
      shift 2
      ;;
    -w|--workspace)
      workspace="$2"
      shift 2
      ;;
    -s|--search-path)
      search_path="$2"
      shift 2
      ;;
    -i|--ignore-errors)
      ignore_errors=true
      shift 1
      ;;
    -d|--dry-run)
      dry_run=true
      shift 1
      ;;
    *)
      echo "Error: Invalid arguments: ${1} ${2}"
      exit 1
  esac
done

if [[ $mode != 'build' && $mode != 'test' && $mode != 'run' ]]; then
  echo "Invalid bazel mode '${mode}'. Valid choices: 'build', 'test', 'run'."
  exit 1
fi

if [[ $bazel != 'bazel' && $bazel != 'dazel' && $bazel != 'auto' ]]; then
  echo "Invalid bazel argument '${bazel}'. Valid choices: 'auto', 'bazel', 'dazel'."
  exit 1
fi

if [[ $bazel == auto ]]; then
  if [ $(which dazel) ]; then
    bazel=dazel
  else
    bazel=bazel
  fi
fi

cd $workspace

targets=$(bazel query 'filter('$pattern', '$search_path')')
echo "Found targets: $targets"

if [[ $mode == 'build' || $mode == 'test' ]]; then
  command="$bazel $mode $targets"
  echo "Running command '$command'."
  if [[ -z $dry_run ]]; then
    $command
  fi
else
  for target in $targets; do
    command="$bazel run $target"
    echo "Running command '$command'."
    if [[ -z $dry_run ]]; then
      if [ $ignore_errors ]; then
        $command || echo "WARNING: Command '$command' failed"
      else
        $command
      fi
    fi
  done
fi
