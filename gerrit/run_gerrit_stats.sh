#!/bin/sh

# Script to create a report of a gerrit repo

set -e

gerrit_server=${1:?}
gerrit_repo=${2:?}
gerrit_user=${3:?}

after_date=2023-01-01

out_dir=~/gerrit_stats

mkdir -p $out_dir

docker run --rm \
   --name gerritstats \
   -v ~/.ssh/id_ed25519:/root/.ssh/id_ed25519 \
   -v $out_dir/gerrit_out:/gerritstats/gerrit_out \
   -v $out_dir/out-html:/gerritstats/out-html \
   zcz3313/gerritstats:latest \
   --server $gerrit_server \
   --project $gerrit_repo \
   --login-name $gerrit_user \
   --output-dir gerrit_out \
   --after-date $after_date

sudo chown -R $(whoami) $out_dir
chgrp -R $(id -g -n) $out_dir

abs_out_dir=$(realpath $out_dir)
echo "Now open file://$abs_out_dir/out-html/index.html"
