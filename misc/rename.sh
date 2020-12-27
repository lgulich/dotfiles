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
  num_repetitions="${4:?}"
  command="mv "\$1" "\${1//${name_old}/${name_new}}""
  for i in {1..num_repetitions}; do
    find "${directory}" -name "*${name_old}*" -exec bash -c "${command}" -- {} \; || true
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


from="${1:?}"
to="${2:?}"
directory="${3:?}"

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

replace_path "${name_old}" "${name_new}" "${directory}" 10
replace_path "${NAME_OLD}" "${NAME_NEW}" "${directory}" 10
replace_path "${NameOld}" "${NameNew}" "${directory}" 10
replace_path "${nameOld}" "${nameNew}" "${directory}" 10
