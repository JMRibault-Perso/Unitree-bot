#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPS_DIR="$ROOT_DIR/deps"

UNITREE_SDK2_URL="https://github.com/unitreerobotics/unitree_sdk2.git"
UNITREE_SDK2_PY_URL="https://github.com/unitreerobotics/unitree_sdk2_python.git"
GO2_WEBRTC_URL="${GO2_WEBRTC_URL:-}"

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

if [ -n "$GO2_WEBRTC_URL" ]; then
  clone_or_pull "$GO2_WEBRTC_URL" "$DEPS_DIR/go2_webrtc_connect"
else
  echo "GO2_WEBRTC_URL is not set; skipping go2_webrtc_connect"
fi
