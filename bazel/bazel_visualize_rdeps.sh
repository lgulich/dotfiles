#!/bin/bash

# Use this script to visualize deps in a bazel workspace

set -e

# Change to bazel workspace root dir if this script is run from bazel
cd "${BUILD_WORKING_DIRECTORY:-.}"

bazel=auto
workspace='.'
depth=2
in='//...'

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
    --of)
      # The rdeps of this target will be visualized.
      of="$2"
      shift 2
      ;;
    --in)
      # Only the rdeps in this target's closure will be visualized.
      in="$2"
      shift 2
      ;;
    --depth)
      depth="$2"
      shift 2
      ;;
    *)
      echo "Error: Invalid arguments: ${1} ${2}"
      exit 1
  esac
done

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

echo "Querying the graph..."
graph_description=$($bazel cquery "rdeps($in, $of, $depth)" --notool_deps --noimplicit_deps --keep_going --output=graph)
echo "Visualizing the graph..."
echo $graph_description | "dot" -Tsvg > rdeps.svg
echo "To visualize the graph, open 'file:///$(pwd)/rdeps.svg' in your browser."
