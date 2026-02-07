#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPS_DIR="$ROOT_DIR/deps"

UNITREE_SDK2_URL="https://github.com/unitreerobotics/unitree_sdk2.git"
UNITREE_SDK2_PY_URL="https://github.com/unitreerobotics/unitree_sdk2_python.git"

mkdir -p "$DEPS_DIR"

clone_or_pull() {
  local url="$1"
  local target="$2"

  if [ -d "$target/.git" ]; then
    git -C "$target" pull --ff-only
  else
    git clone "$url" "$target"
  fi
}

clone_or_pull "$UNITREE_SDK2_URL" "$DEPS_DIR/unitree_sdk2"
clone_or_pull "$UNITREE_SDK2_PY_URL" "$DEPS_DIR/unitree_sdk2_python"

if [ -f "$ROOT_DIR/.gitmodules" ]; then
  echo "g1_webrtc_connect is tracked as a git submodule."
  echo "Run: git submodule update --init --recursive"
fi
