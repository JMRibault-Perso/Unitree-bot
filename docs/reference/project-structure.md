# Project Structure Reference

## Overview

This document explains the organization of the Unitree G1 SDK codebase.

## Directory Layout

```
unitree_sdk2/
├── docs/                           # 📚 All documentation (START HERE)
│   ├── README.md                   # Main documentation index
│   ├── api/                        # API references
│   │   └── robot-discovery.md      # Discovery API (SINGLE SOURCE OF TRUTH)
│   ├── guides/                     # How-to guides
│   │   ├── slam-navigation.md      # SLAM features
│   │   ├── testing-guide.md        # Testing infrastructure
│   │   └── ...
│   ├── reference/                  # Technical references
│   │   └── project-structure.md    # This file
│   └── archived/                   # Old/deprecated docs (DO NOT USE)
│
├── g1_app/                         # 🤖 Main web controller application
│   ├── core/                       # Core functionality
│   │   ├── robot_discovery.py      # Web server discovery loop
│   │   ├── fsm_validator.py        # FSM state validation
│   │   └── webrtc_manager.py       # WebRTC connection handling
│   ├── utils/                      # Utilities
│   │   ├── robot_discovery.py      # ⭐ Centralized discovery API (USE THIS)
│   │   ├── arp_discovery.py        # Low-level ARP/multicast
│   │   └── ...
│   ├── slam/                       # SLAM functionality
│   │   ├── map_builder.py          # Map building
│   │   ├── relocation.py           # Relocation handling
│   │   └── navigation.py           # Waypoint navigation
│   ├── ui/                         # Web UI
│   │   ├── static/                 # HTML/CSS/JS
│   │   └── templates/              # HTML templates
│   └── server.py                   # FastAPI web server (port 3000)
│
├── g1_tests/                       # 🧪 All test scripts
│   ├── robot_test_helpers.py       # Test utilities (ALL TESTS USE THIS)
│   │   └── RobotTestConnection     # Auto-discovery context manager
│   ├── test_discovery_monitor.py   # Discovery state monitoring
│   ├── test_relocation_detection.py # SLAM relocation tests
│   ├── test_api_1102_heading.py    # API-specific tests
│   ├── test_slam_*.py              # SLAM test suite
│   └── ...
│
├── slam_example/                   # SLAM code examples
│   ├── navigate_waypoint.py        # Navigation examples
│   └── ...
│
├── maps/                           # 🗺️ Saved SLAM maps
│   └── [map_name]/                 # Per-map directory
│       ├── map.pgm                 # Occupancy grid
│       ├── map.yaml                # Map metadata
│       └── waypoints.json          # Waypoint data
│
├── _scripts/                       # Utility scripts
│   ├── diagnose_dds.sh             # DDS diagnostics (EDU only)
│   └── quick_test.sh               # Quick connectivity test
│
├── example/                        # SDK examples (C++)
│   ├── g1/                         # G1-specific examples
│   │   ├── high_level/             # Client API examples
│   │   └── low_level/              # Direct motor control
│   ├── go2/, h1/, b2/              # Other robot examples
│   └── ...
│
├── include/                        # C++ SDK headers
│   └── unitree/
│       ├── robot/                  # High-level clients
│       │   ├── g1/                 # G1 clients
│       │   ├── go2/                # GO2 clients
│       │   └── ...
│       └── idl/                    # Auto-generated DDS messages
│
├── lib/                            # Prebuilt SDK libraries
│   ├── x86_64/                     # x86_64 binaries
│   └── aarch64/                    # ARM64 binaries
│
├── thirdparty/                     # Third-party dependencies
│   ├── lib/                        # CycloneDDS, yaml-cpp, etc.
│   └── include/                    # Third-party headers
│
├── build/                          # CMake build output
│   └── bin/                        # Compiled executables
│
├── cyclonedds.xml                  # DDS configuration
├── README.md                       # Project README
└── .github/
    └── copilot-instructions.md     # AI agent instructions

```

## Key Components

### Documentation (`docs/`)

**Purpose**: Centralized documentation for all users and AI agents.

**Structure**:
- `README.md` - Main index, start here
- `api/` - API references (authoritative specs)
- `guides/` - How-to guides (tutorials)
- `reference/` - Technical references (this file)
- `archived/` - Old docs (deprecated, do not use)

**Usage**: Always read `docs/README.md` first.

### Web Controller (`g1_app/`)

**Purpose**: Python-based web controller replicating Unitree Explore app functionality.

**Key Files**:
- `server.py` - FastAPI server on port 3000
- `core/robot_discovery.py` - Background discovery loop
- `utils/robot_discovery.py` - **Centralized discovery API** (use this)
- `slam/` - SLAM functionality (maps, waypoints, navigation)
- `ui/` - Web interface (HTML/JS)

**Architecture**: WebRTC + HTTP/WebSocket (not DDS SDK).

### Test Helpers (`g1_tests/robot_test_helpers.py`)

**Purpose**: Common utilities for all test scripts.

**Usage**:
```python
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2/g1_tests')
from robot_test_helpers import RobotTestConnection

async with RobotTestConnection() as robot:
    # robot.ip, robot.mac, robot.mode auto-discovered
    pass
```

**All test scripts should use this** - don't hardcode IPs.

### Test Scripts (`g1_tests/test_*.py`)

**Purpose**: Validation and testing of robot features.

**Organization**:
- `test_discovery_*.py` - Discovery tests
- `test_slam_*.py` - SLAM tests
- `test_api_*.py` - API-specific tests
- `test_relocation_*.py` - Relocation tests

**Run from g1_tests directory** with `cd g1_tests && python3 test_<name>.py`.

### SLAM Examples (`slam_example/`)

**Purpose**: SLAM implementation examples and map building tools.

**Files**:
- `G1_SLAM_IMPLEMENTATION.py` - Complete SLAM API reference and implementation
- `build_room_map.py` - Interactive map building script
- `navigate_waypoint.py` - Navigation examples

### SLAM Maps (`maps/`)

**Purpose**: Persistent storage of built maps and waypoints.

**Structure**:
```
maps/
  my_room/
    map.pgm         # Occupancy grid (PGM image)
    map.yaml        # Metadata (resolution, origin)
    waypoints.json  # Named waypoints
```

### C++ SDK (`example/`, `include/`, `lib/`)

**Purpose**: Native C++ interface to robot (EDU models only).

**Note**: G1 Air models don't support DDS SDK - use Python web controller instead.

**Key Directories**:
- `example/` - C++ example programs
- `include/unitree/robot/` - High-level client APIs
- `lib/` - Prebuilt SDK binaries
- `build/bin/` - Compiled executables

## File Naming Conventions

### Documentation
- `docs/api/*.md` - API references (authoritative)
- `docs/guides/*.md` - How-to guides
- `docs/reference/*.md` - Technical references
- `docs/archived/*.md` - Deprecated docs (DO NOT USE)

### Python Code
- `g1_app/` - Application code (web controller)
- `robot_test_helpers.py` - Test utilities
- `test_*.py` - Test scripts
- `build_*.py` - Build/utility scripts

### C++ Code
- `example/*/` - Examples by robot type
- `include/unitree/robot/*/` - Client headers
- `include/unitree/idl/*/` - Auto-generated messages

## Import Patterns

### Python

**Correct** (use centralized discovery):
```python
from g1_app.utils.robot_discovery import discover_robot, wait_for_robot
```

**Deprecated** (old API):
```python
from g1_app.utils.arp_discovery import discover_robot_ip  # ❌ Don't use
```

### C++ (EDU Models Only)

```cpp
#include "unitree/robot/channel/channel_factory.h"
#include "unitree/robot/g1/loco/loco_client.hpp"

unitree::robot::ChannelFactory::Instance()->Init(0, "eth0");
unitree::robot::g1::LocoClient client;
client.Init();
```

## Configuration Files

### `cyclonedds.xml`
DDS configuration for EDU models. Not used by G1 Air.

### `maps_config.json`
SLAM maps metadata and configuration.

### `.github/copilot-instructions.md`
Instructions for AI coding assistants. Points to `docs/README.md`.

## Build Artifacts

### `build/`
CMake build output. Generated by:
```bash
mkdir build && cd build
cmake .. && make -j$(nproc)
```

### `__pycache__/`
Python bytecode cache (git-ignored).

## Archive Directories

### `archive/`
Old research, logs, pcap analysis. Not actively maintained.

### `docs/archived/`
Deprecated documentation. Read `docs/archived/README.md` for context.

### `unitree_docs/`, `unitree_full_pull/`
SDK documentation snapshots. Reference only.

## See Also

- [Main Documentation Index](../README.md) - Start here
- [Robot Discovery API](../api/robot-discovery.md) - Discovery details
- [Testing Guide](../guides/testing-guide.md) - How to write tests
- [SLAM Navigation Guide](../guides/slam-navigation.md) - SLAM features
