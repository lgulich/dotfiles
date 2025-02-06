# shellcheck shell=sh

cd_and_ls() {
  "cd" "$1" && ls
}

show_largest_files() {
  sudo du -sh .[^.]* | sort -rh | head -n ${1:-10}
}

serve_file() {
  file_path="$(realpath ${1:?})"
  file_parentdir="$(dirname ${file_path})"
  file_basename="$(basename ${file_path})"

  ip=$(hostname -I | awk '{print $1}')
  port=8005
  echo "See file at: 'http://${ip}:${port}/${file_basename}'"
  python3 -m http.server ${port} --directory ${file_parentdir}
}

download_folder() {
  folder_url=${1:?}
  wget --recursive --no-parent --reject "index.html" ${folder_url}
}

# Run the cursor command and suppress background process output completely
cursor() {
  (nohup /opt/cursor/cursor.AppImage --no-sandbox "$@" > /dev/null 2>&1 &)
}
