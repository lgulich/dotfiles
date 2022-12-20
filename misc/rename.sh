#!/bin/bash

set -e

replace_content() {
  name_old="${1:?}"
  name_new="${2:?}"
  directory="${3:?}"
  find "${directory}" \( -type d -name .git -prune \) -o -type f -print0 | xargs -0 sed -i "s/${name_old}/${name_new}/g"
}

replace_path() {
  name_old="${1:?}"
  name_new="${2:?}"
  directory="${3:?}"

  files="$(find ${directory} | grep ${name_old})"
  new_files="$(echo $files | sed s/${name_old}/${name_new}/g)"
  files=($files)
  new_files=($new_files)

  for ((i=0; i<${#files[@]}; i++)); do
    mkdir -p "$(dirname $new_files)"
    mv "${files[i]}" "${new_files[i]}"
  done
}

convert_to_snake_case() {
 echo "${1:?}" | tr [A-Z] [a-z] | sed -r 's/ /_/g'
}

convert_to_UpperCamelCase() {
 echo "${1:?}" | sed -r 's/(^|_)([a-z])/\U\2/g'
}

convert_to_lowerCamelCase() {
 echo "${1:?}" | sed -r 's/([a-z]+)_([a-z])([a-z]+)/\1\U\2\L\3/'
}

convert_to_CAPITAL_CASE() {
 echo "${1:?}" | tr [a-z] [A-Z]
}

set -eo pipefail

print_usage() {
  echo "Renames a substring in all contained directories recursively in both"
  echo "file paths and file contents."
  echo ""
  echo "Usage: $0 --from <from> --to <to> [-repetitions=<repetitions>] <path>"
  echo "  -f,--from         old substring, in snake case"
  echo "  -t,--to           new substring, in snake case"
  echo "  -h,--help         show this help message"
}

short="f:,t:,h"
long="from:,to:,help"
arguments=$(getopt -a -n rename --options $short --longoptions $long -- "$@")
eval set -- "$arguments"
while :
do
  case "$1" in
    -f | --from )
      from="${2:?}"
      shift 2
      ;;
    -t | --to )
      to="${2:?}"
      shift 2
      ;;
    -h | --help)
      print_usage
      exit 0
      ;;
    --)
      shift;
      break
      ;;
    *)
      echo "Unexpected option: $1"
      print_usage
      exit 1
      ;;
  esac
done

directory="${1:?}"

name_old="$(convert_to_snake_case "${from}")"
NAME_OLD="$(convert_to_CAPITAL_CASE "${name_old}")"
NameOld="$(convert_to_UpperCamelCase "${name_old}")"
nameOld="$(convert_to_lowerCamelCase "${name_old}")"

name_new="$(convert_to_snake_case "${to}")"
NAME_NEW="$(convert_to_CAPITAL_CASE "${name_new}")"
NameNew="$(convert_to_UpperCamelCase "${name_new}")"
nameNew="$(convert_to_lowerCamelCase "${name_new}")"

replace_content "${name_old}" "${name_new}" "${directory}"
replace_content "${NAME_OLD}" "${NAME_NEW}" "${directory}"
replace_content "${NameOld}" "${NameNew}" "${directory}"
replace_content "${nameOld}" "${nameNew}" "${directory}"

replace_path "${name_old}" "${name_new}" "${directory}"
replace_path "${NAME_OLD}" "${NAME_NEW}" "${directory}"
replace_path "${NameOld}" "${NameNew}" "${directory}"
replace_path "${nameOld}" "${nameNew}" "${directory}"
