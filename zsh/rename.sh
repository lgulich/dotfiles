#!/bin/sh

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

directory="${1:?}"
name_old=compp
name_new=arc
NAME_OLD=COMPP
NAME_NEW=ARC
NameOld=Compp
NameNew=Arc
nameOld=compp
nameNew=arc

replace_content "${name_old}" "${name_new}" "${directory}"
replace_content "${NAME_OLD}" "${NAME_NEW}" "${directory}"
replace_content "${NameOld}" "${NameNew}" "${directory}"
replace_content "${nameOld}" "${nameNew}" "${directory}"

replace_path "${name_old}" "${name_new}" "${directory}" 10
replace_path "${NAME_OLD}" "${NAME_NEW}" "${directory}" 10
replace_path "${NameOld}" "${NameNew}" "${directory}" 10
replace_path "${nameOld}" "${nameNew}" "${directory}" 10


