# Project Organization Summary

**Date**: February 5, 2026  
**Status**: ✅ Complete

## 📁 Directory Structure - Final Organization

```
unitree_sdk2/
├── docs/                           # 📚 All documentation
│   ├── README.md                   # Main index (START HERE)
│   ├── api/
│   │   └── robot-discovery.md      # Discovery API (SINGLE SOURCE OF TRUTH)
│   ├── guides/
│   │   ├── slam-navigation.md      # SLAM/mapping
│   │   ├── testing-guide.md        # Testing infrastructure
│   │   └── ...
│   ├── reference/
│   │   └── project-structure.md    # Code organization
│   └── archived/                   # Deprecated docs
│
├── g1_app/                         # 🤖 Web controller application
│   ├── core/
│   ├── utils/robot_discovery.py    # ⭐ Centralized discovery (USE THIS)
│   ├── slam/
│   ├── ui/
│   ├── server.py                   # FastAPI (port 3000)
│   └── ...
│
├── g1_tests/                       # 🧪 All test scripts
│   ├── robot_test_helpers.py       # Test utilities
│   ├── test_discovery_monitor.py
│   ├── test_slam_*.py
│   ├── test_api_*.py
│   ├── test_relocation_*.py
│   └── ...
│
├── slam_example/                   # SLAM examples
├── maps/                           # 🗺️ Saved maps
├── example/                        # C++ SDK examples
├── build/                          # CMake build output
├── README.md                       # Project README
└── cyclonedds.xml                  # DDS configuration
```

## 🔄 Changes Made

### 1. Test File Organization
**Moved to `g1_tests/`**:
- ✅ `test_api_1102_heading.py`
- ✅ `test_discovery_monitor.py`
- ✅ `test_enhanced_discovery.py`
- ✅ `test_map_build_with_joystick.py`
- ✅ `test_relocation_detection.py`
- ✅ `test_relocation_detection_mock.py`
- ✅ `test_slam_save_load.py`
- ✅ `test_slam_topics_realtime.py`
- ✅ `test_slam_workflow.py`
- ✅ `test_teaching_action_list.py`
- ✅ `robot_test_helpers.py`

### 2. Documentation Files
**Moved to `docs/guides/`**:
- ✅ `3D_VIEWER_IMPLEMENTATION_GUIDE.md`
- ✅ `README_NAVIGATION_SYSTEM.md`

### 3. SLAM Implementation & Examples
**Moved to `slam_example/`**:
- ✅ `G1_SLAM_IMPLEMENTATION.py` - Complete API reference
- ✅ `build_room_map.py` - Interactive map builder

### 4. Documentation Updates
Updated in multiple documentation files:
- ✅ `docs/README.md` - All example paths
- ✅ `docs/api/robot-discovery.md` - File references
- ✅ `docs/guides/slam-navigation.md` - SLAM paths
- ✅ `docs/guides/testing-guide.md` - Test paths
- ✅ `docs/reference/project-structure.md` - Directory tree
- ✅ `README.md` - Example commands
- ✅ `.github/copilot-instructions.md` - AI instructions

## 📍 Single Source of Truth

### Discovery
```python
from g1_app.utils.robot_discovery import discover_robot
robot = discover_robot()  # {ip, mac, mode, online}
```

### Testing
All tests now in: `g1_tests/test_*.py`

All imports: `from g1_tests.robot_test_helpers import RobotTestConnection`

### Documentation
Start here: `docs/README.md`

## 🚀 Quick Reference

### Running Tests
```bash
# From project root
cd g1_tests

# Run any test
python3 test_slam_topics_realtime.py
python3 test_discovery_monitor.py
python3 test_relocation_detection.py
```

### Updating Code
**Old way** (❌ DON'T USE):
```python
import sys
sys.path.insert(0, '.')
from robot_test_helpers import ...
```

**New way** (✅ USE THIS):
```python
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2/g1_tests')
from robot_test_helpers import RobotTestConnection
```

Or run from within `g1_tests/`:
```bash
cd g1_tests && python3 your_test.py
```

## ✅ Verification

```bash
# Verify no test files in root
find /root/G1/unitree_sdk2 -maxdepth 1 -name "test_*.py" -o -name "robot_test_helpers.py"
# Result: (empty - all moved)

# Verify files in g1_tests
ls /root/G1/unitree_sdk2/g1_tests/test_*.py
# Result: 11 test files present

# Verify robot_test_helpers.py
ls /root/G1/unitree_sdk2/g1_tests/robot_test_helpers.py
# Result: present
```

## 📝 For AI Agents

When working with this project:

1. **Start with**: `docs/README.md`
2. **Discovery API**: `g1_app/utils/robot_discovery.py` (SINGLE SOURCE OF TRUTH)
3. **All tests**: In `g1_tests/` directory
4. **Web controller**: `g1_app/` with server on port 3000
5. **SLAM code**: `slam_example/` and `g1_app/slam/`

All documentation links have been updated to reflect the new structure.

## 🎯 Organization Principles

1. **Centralization**: One discovery method, one test directory, one docs structure
2. **Clarity**: Files in logical places with clear purposes
3. **Consistency**: All paths updated in all documentation
4. **Discoverability**: Start at `docs/README.md` for any topic

---

**This organization is final and all documentation reflects these changes.**
