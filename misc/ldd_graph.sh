#!/bin/bash

set -e

find_so_path() {
  local parent_so_path="${1:?}"
  local child_so_name="${2:?}"

  ldd_output=$(ldd "$so_path" | grep "$child_so_name")

  if [[ "${ldd_output}" == *"=>"* ]]; then
    # ldd_output could be "=> path/to/lib.so" or "=> Not found"
    echo ${ldd_output} | awk '{print $3}'
  else
    echo "Embedded"
  fi
}

ldd_recursive() {
  local so_file=${1:?}
  local so_path=${2:?}
  local indent=${3:-""}

  if [ -f "${so_path}" ]; then
    so_runpath=$(readelf -d "${so_path}" | awk '/RUNPATH/ {print $NF}' | tr -d '[]')
    so_rpath=$(readelf -d "${so_path}" | awk '/RPATH/ {print $NF}' | tr -d '[]')
    so_direct_deps=$(readelf -d "${so_path}" | awk '/NEEDED/ {print $NF}' | tr -d '[]')
  else
    # so_path="Not found"
    so_rpath="N/A"
    so_runpath="N/A"
    so_direct_deps=""
  fi

  echo "${indent}${so_file}:"
  echo "${indent}    path: ${so_path}"
  echo "${indent}    rpath: ${so_rpath}"
  echo "${indent}    runpath: ${so_runpath}"
  echo "${indent}    deps:"

  for direct_dep in ${so_direct_deps}; do
    direct_dep_path=$(find_so_path "${so_path}" "${direct_dep}")
    ldd_recursive "$direct_dep" "${direct_dep_path}" "${indent}        "
  done
}

print_usage() {
  echo "Show the dependencies of a shared object as a graph."
  echo ""
  echo "Usage: $0 <so_path>"
  echo "  -h,--help         show this help message"
  echo "  <so_path>            shared object that should be analyzed"
}

script_dir="$(dirname "$(readlink -f "$0")")"

so_path="${1:?}"

output_yaml=graph.yaml
output_image=graph.svg

[ -f ${output_yaml} ] && rm ${output_yaml}
ldd_recursive $(basename ${so_path}) ${so_path} "" >> ${output_yaml}
${script_dir}/plot_yaml_graph.py ${output_yaml} ${output_image}
