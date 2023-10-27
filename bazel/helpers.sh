#!/bin/sh

bazel_regex() {
  bazel_regex.sh $@ --bazel bazel
}

dazel_regex() {
  bazel_regex.sh $@ --bazel dazel
}

bazel_visualize() {
  bazel_visualize.sh $@ --bazel bazel
}

dazel_visualize() {
  bazel_visualize.sh $@ --bazel dazel
}
