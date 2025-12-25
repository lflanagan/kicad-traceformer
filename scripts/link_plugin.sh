#!/usr/bin/env bash
set -euo pipefail

# Create a symlink from the repo's plugin folder to the KiCad 3rdparty plugins path.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${REPO_DIR}/plugin"
TARGET="${HOME}/Documents/KiCad/9.0/3rdparty/plugins/ionetlistkicadplugin"

echo "Linking plugin:"
echo "  source: ${SRC}"
echo "  target: ${TARGET}"

mkdir -p "$(dirname "${TARGET}")"

if [ -L "${TARGET}" ] || [ -d "${TARGET}" ]; then
  echo "Removing existing target ${TARGET}"
  rm -rf "${TARGET}"
fi

ln -s "${SRC}" "${TARGET}"
echo "Done. Restart KiCad or refresh plugins to pick up changes."
