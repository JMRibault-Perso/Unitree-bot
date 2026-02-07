# G1 Robot Test Suite

Organized test suite for G1 robot development and validation.

## 📁 Directory Structure

```
G1_tests/
├── slam/           # SLAM mapping and navigation tests
├── motion/         # Motion control and FSM tests
├── arm/            # Arm control and teach mode tests
├── sensors/        # Sensor tests (LiDAR, IMU, cameras)
├── utilities/      # Helper scripts and monitoring tools
└── obsolete/       # Archived/deprecated tests for reference
```

## 🎯 Test Standards

All tests follow the standardized pattern defined in `../TEST_SCRIPT_STANDARDS.md`:

- ✅ Use `robot_test_helpers.py` for connections
- ✅ Auto ARP discovery (no hardcoded IPs)
- ✅ Proper disconnect handling (`disconnect()` not `close()`)
- ✅ Context manager pattern for resource cleanup
- ✅ Graceful timing (0.2s before disconnect, 0.1s after API calls)

## 🚀 Quick Start

```bash
# Navigate to specific test category
cd G1_tests/slam/

# Run a test
python3 test_navigation_v2.py

# Most tests support --help
python3 test_navigation_v2.py --help
```

## 📚 Category Guides

Each subdirectory contains:
- `README.md` - Detailed category documentation
- Test scripts following standardized pattern
- Example commands and usage

## 🔧 Common Patterns

### Basic Test Script
```python
import asyncio
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from robot_test_helpers import RobotTestConnection, SLAM_API

async def main():
    async with RobotTestConnection() as robot:
        # Your test code here
        response = await robot.send_slam_request(SLAM_API['START_MAPPING'], {})
        print(f"✅ Result: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Running Multiple Tests
```bash
# From G1_tests/
for test in slam/test_*.py; do
    echo "Running $test"
    python3 "$test"
done
```

## 🧹 Maintenance

- **Adding new tests**: Place in appropriate category, follow standardized pattern
- **Updating tests**: Use `robot_test_helpers.py` for all WebRTC connections
- **Archiving tests**: Move obsolete tests to `obsolete/` with explanatory comment

## 📖 Related Documentation

- `../TEST_SCRIPT_STANDARDS.md` - Standard patterns and conventions
- `../robot_test_helpers.py` - Core helper module
- `../QUICK_START.md` - General G1 setup guide
