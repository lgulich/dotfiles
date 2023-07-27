#!/bin/sh

bazel_regex() {
  bazel_regex.sh $@ -b bazel
}

dazel_regex() {
  bazel_regex.sh $@ -b dazel
}
