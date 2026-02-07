#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

python3 -m pip install --upgrade pip
python3 -m pip install -r "$ROOT_DIR/requirements.txt"

"$ROOT_DIR/scripts/pull_deps.sh"

git -C "$ROOT_DIR" submodule update --init --recursive

echo "Bootstrap complete. Activate with: source $VENV_DIR/bin/activate"
