# Obsolete Tests Archive

This directory contains old/deprecated test files kept for reference only.

These tests are either:
- Replaced by standardized versions in parent directories
- Using outdated connection patterns
- Redundant/duplicate functionality
- Experimental/incomplete implementations

## 📚 Replacement Guide

If you need functionality from an obsolete test, use the standardized version:

### Old Tests → New Standardized Tests

**Motion Control:**
- `../g1_simple_control.py` → `g1_tests/motion/simple_control.py`
- `../g1_quick_control.py` → `g1_tests/motion/simple_control.py`
- `../g1_controller.py` → Use `simple_control.py` + standardized helpers

**SLAM:**
- `../test_navigation.py` → `g1_tests/slam/test_navigation_v2.py`
- `../stop_slam.py` → `g1_tests/slam/stop_slam_v2.py`
- `../cancel_navigation.py` → `g1_tests/slam/cancel_navigation_v2.py`
- `../slam_mapper.py` → `g1_tests/slam/start_mapping.py`

**Arm Control:**
- `../enable_teach_mode.py` → `g1_tests/arm/enable_teach_mode.py`
- `../show_available_actions.py` → `g1_tests/arm/list_actions.py`
- `../test_arm_*.py` → Consolidated into `g1_tests/arm/` directory

**Utilities:**
- `../discover_robot.py` → `g1_tests/utilities/discover_robot.py`
- `../list_available_topics.py` → `g1_tests/utilities/list_topics.py`
- `../listen_all_topics.py` → `g1_tests/sensors/listen_all.py`

## 🔧 Why Obsolete?

Common issues with old tests:
1. **Wrong disconnect pattern**: Used `close()` instead of `disconnect()`
2. **Hardcoded IPs**: No ARP auto-discovery
3. **Inconsistent patterns**: Each test had different connection code
4. **No context manager**: Manual connection/disconnection prone to errors
5. **Missing error handling**: No graceful timing delays

## ✅ Standardized Pattern

All new tests follow `robot_test_helpers.py`:

```python
import asyncio
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2')
from robot_test_helpers import RobotTestConnection, SLAM_API

async def main():
    async with RobotTestConnection() as robot:
        # Auto ARP discovery
        # Proper WebRTC connection
        # Graceful disconnect with timing
        response = await robot.send_slam_request(SLAM_API['...'], {})

if __name__ == "__main__":
    asyncio.run(main())
```

See `../TEST_SCRIPT_STANDARDS.md` for full documentation.
