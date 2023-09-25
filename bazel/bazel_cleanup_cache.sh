#! /bin/bash
# Clean up everything in CACHE_DIR last accessed more than DAYS days ago.
# Also removes files with bogus timestamps in the future.

set -e

cache_dir=~/.cache/bazel
days=15

while [ $# -gt 0 ]; do
  case "$1" in
    -c|--cache-dir)
      cache_dir="$2"
      shift 2
      ;;
    -d|--days)
      days="$2"
      shift 2
      ;;
    *)
      echo "Error: Invalid arguments: ${1} ${2}"
      exit 1
  esac
done

readonly dirlist="$(tempfile)"

# something is dropping non-writable directories in the cache
find "${cache_dir}" -type d -a \! -writable -fprint0 ${dirlist}
if [[ -s ${dirlist} ]]; then
  echo "Fixing $(tr -cd '\0' < ${dirlist} | wc -c) non-writeable directories"
  xargs -0 -a "${dirlist}" chmod +w
fi

echo "Cleaning files in '${cache_dir}' with atime >${days} days"
find "${cache_dir}" \( -type f -o -type l \) -a \
  \( -atime "+${days}" -o -newermt "1 day" \) -print0 |
  xargs -r -0 rm

echo -n "Cleaning empty directories..."
while true; do
  # never remove CACHE_DIR itself
  find "${cache_dir}" -type d \! -path "${cache_dir}" -empty -fprint0 ${dirlist}
  if [[ -s ${dirlist} ]]; then
     echo -n '.'
     xargs -0 -a "${dirlist}" rmdir
   else
     break;
  fi
done
echo " done."
rm "${dirlist}"
