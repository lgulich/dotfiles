#!/bin/bash

set -e

local_path=${1:?Please provide a local path to upload}
remote_path=${2:?Please provide a remote path to upload to}

file_name=$(basename ${local_path})
remote_file_name=${3:-${file_name}}

echo "Uploading '${local_path}' to '${remote_path}/${remote_file_name}'"
read -r -p "Are you sure you want to continue? [Y/n] " ok
if [[ "${ok}" == "n" ]]; then
  echo "Aborting..."
  exit 0
fi

curl \
  --progress-bar \
  -u${ARTIFACTORY_USER}:${ARTIFACTORY_SECRET} \
  -T ${local_path} \
  ${remote_path}/${remote_path_name} \
  | cat

echo "Upload complete."
ehco "Artifactory URL: ${ARTIFACTORY_URL}"
