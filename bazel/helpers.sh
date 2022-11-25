#!/bin/sh

bazel_build_regex() {
  local target_regex=${1:?}
  local targets="$(bazel query //extensions/... | grep -E "$target_regex")"
  bazel build $targets
}
