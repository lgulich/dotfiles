#!/bin/sh

bazel_regex() {
  bazel_regex.sh $@ --bazel bazel
}

dazel_regex() {
  bazel_regex.sh $@ --bazel dazel
}
