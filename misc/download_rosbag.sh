#!/bin/bash

# Use this tool to download a rosbag from a URL.

set -e

url=${1:?}
destination=${2:?}

# Remove trailing slash if present
path=${url%/}
destination=${destination%/}

name=$(basename $url)
metadata_file_name=metadata.yaml
mcap_file_name=${name}_0.mcap

rm -rf ${destination}/${name}
mkdir -p ${destination}/${name}
wget ${url}/${metadata_file_name} -P ${destination}/${name}
wget ${url}/${mcap_file_name} -P ${destination}/${name}
