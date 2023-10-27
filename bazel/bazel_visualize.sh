#!/bin/bash

# Use this script to visualize deps/rdeps in a bazel workspace.
# Examples:
#   $ bazel_visualize deps --of //foo --output labels
#   $ bazel_visualize rdeps --of //foo --in //... --depth 2 --output graph
#   $ bazel_visualize somepath --of //foo --to //bar
#   $ bazel_visualize allpaths --of //foo --to //bar

set -e

# Change to bazel workspace root dir if this script is run from bazel
cd "${BUILD_WORKING_DIRECTORY:-.}"


# Parse mode as positional CLI argument.
mode=${1:?}
shift 1

# Parse remaining CLI arguments.
bazel=auto
workspace='.'
depth=2
output=png
in='//...'
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
      # The deps/rdeps of this target will be visualized.
      of="$2"
      shift 2
      ;;
    --to)
      to="$2"
      shift 2
      ;;
    --in)
      # Only the deps/rdeps in this target's closure will be visualized.
      in="$2"
      shift 2
      ;;
    --depth)
      depth="$2"
      shift 2
      ;;
    --output)
      output="$2"
      shift 2
      ;;
    *)
      echo "Error: Invalid arguments: ${1} ${2}"
      exit 1
  esac
done

if [[ $bazel != 'bazel' && $bazel != 'dazel' && $bazel != 'auto' ]]; then
  echo "Error: Invalid 'bazel' argument '${bazel}'. Valid choices: 'auto', 'bazel', 'dazel'."
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
if [[ $mode == deps ]]; then
  graph_description=$($bazel cquery "deps($of)" --notool_deps --noimplicit_deps --keep_going --output=$output)
elif [[ $mode == rdeps ]]; then
  graph_description=$($bazel cquery "rdeps($in, $of, $depth)" --notool_deps --noimplicit_deps --keep_going --output=$output)
elif [[ $mode == somepath || $mode == allpaths ]]; then
  graph_description=$($bazel cquery "$mode($of, $to)" --notool_deps --noimplicit_deps --keep_going --output=$output)
else
  echo "Error: Invalid 'mode' argument '${mode}'. Valid choices: 'deps', 'rdeps', 'somepath', 'allpaths'."
  exit 1
fi

if [[ $output != graph ]]; then
  echo "Found '$mode':"
  echo "$graph_description"
  exit 0
elif [[ $output == graph ]]; then
  image_path=$(pwd)/graph_$mode.svg
  echo "Visualizing the graph..."
  echo $graph_description | "dot" -Tsvg > $image_path
  echo "To visualize the graph, open 'file://$image_path' in your browser."
fi
