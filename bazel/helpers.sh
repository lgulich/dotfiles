#!/bin/sh

bazel_build_regex() {
  local target_regex=${1:?}
  local targets="$(bazel query //extensions/... | grep -E "$target_regex")"
  echo "Found targets: $targets"
  echo "Building...."
  bazel build "$targets"
}
