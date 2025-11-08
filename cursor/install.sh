#!/bin/bash

set -euo pipefail

cursor_version="latest"
ext_name="DunderDev.sync-everything"
ext_version="0.3.1"

tmp_dir="$(mktemp -d)"
deb_path="$tmp_dir/cursor.deb"
dmg_path="$tmp_dir/cursor.dmg"
vsix_path="$tmp_dir/${ext_name}-${ext_version}.vsix"
dmg_mount_point=""

cleanup() {
  if [[ -n "$dmg_mount_point" ]] && [[ -d "$dmg_mount_point" ]]; then
    hdiutil detach "$dmg_mount_point" -quiet 2>/dev/null || true
  fi
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

echo "Installing cursor agent."
curl https://cursor.com/install -fsS | bash

os_type="$(uname -s)"
case "$os_type" in
  Linux*)
    platform="linux"
    ;;
  Darwin*)
    platform="macos"
    ;;
  *)
    echo "Unsupported OS: $os_type"
    exit 1
    ;;
esac

if [[ "$platform" == "linux" ]]; then
  echo "Installing Cursor ${cursor_version} for Linux..."
  curl -fsSL -o "$deb_path" "https://api2.cursor.sh/updates/download/golden/linux-x64-deb/cursor/${cursor_version}"
  sudo apt-get update -y
  sudo apt-get install -y "$deb_path"
elif [[ "$platform" == "macos" ]]; then
  echo "Installing Cursor ${cursor_version} for macOS..."
  curl -fsSL -L -o "$dmg_path" "https://api2.cursor.sh/updates/download/golden/darwin-arm64/cursor/${cursor_version}"
  dmg_mount_point=$(hdiutil attach "$dmg_path" -nobrowse -noverify -noautoopen 2>&1 | tail -n 1 | awk -F '\t' '{print $3}')
  if [[ -z "$dmg_mount_point" ]] || [[ ! -d "$dmg_mount_point" ]]; then
    echo "error: failed to mount DMG"
    exit 1
  fi
  app_dir=$(find "$dmg_mount_point" -name "Cursor.app" -type d | head -n 1)
  if [[ -z "$app_dir" ]]; then
    echo "error: could not find Cursor.app in the DMG"
    exit 1
  fi
  sudo rm -rf "/Applications/Cursor.app"
  sudo cp -R "$app_dir" /Applications/
  hdiutil detach "$dmg_mount_point" -quiet
  dmg_mount_point=""
  echo "Cursor installed to /Applications/Cursor.app"
fi

echo "Installing VSIX extension ${ext_name} v${ext_version}..."
ext_path=$(echo "$ext_name" | sed 's/\./\//')
curl -fsSL -o "$vsix_path" "https://open-vsx.org/api/${ext_path}/${ext_version}/file/${ext_name}-${ext_version}.vsix"
cursor --install-extension "$vsix_path" || {
  echo "error: failed to install extension"
  exit 1
}

echo "Installation complete!"
cursor --version

