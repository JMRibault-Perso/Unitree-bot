"""Path helpers for local dev layout."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional


def get_repo_root() -> Path:
    """Return the repository root that contains g1_app/."""
    return Path(__file__).resolve().parents[2]


def get_deps_dir() -> Path:
    """Return the deps/ directory under the repo root."""
    return get_repo_root() / "deps"


def get_webrtc_paths() -> List[str]:
    """Return candidate paths to the go2_webrtc_connect library."""
    paths: List[str] = []

    env_path = os.getenv("G1_WEBRTC_PATH") or os.getenv("UNITREE_WEBRTC_PATH")
    if env_path:
        paths.append(env_path)

    repo_root = get_repo_root()
    paths.append(str(get_deps_dir() / "go2_webrtc_connect"))
    paths.append(str(repo_root / "libs" / "go2_webrtc_connect"))
    paths.append("/root/G1/go2_webrtc_connect")

    # Deduplicate while preserving order
    seen = set()
    unique_paths: List[str] = []
    for path in paths:
        if path and path not in seen:
            seen.add(path)
            unique_paths.append(path)

    return unique_paths


def get_cyclonedds_uri() -> Optional[str]:
    """Return CYCLONEDDS_URI based on env or local deps if available."""
    env_uri = os.getenv("CYCLONEDDS_URI")
    if env_uri:
        return env_uri

    candidates = [
        get_deps_dir() / "unitree_sdk2" / "cyclonedds.xml",
        get_repo_root() / "cyclonedds.xml",
    ]

    for candidate in candidates:
        if candidate.exists():
            return f"file://{candidate}"

    return None
