# Testing Guide

## Overview

This guide covers testing infrastructure, writing tests, and running test suites for the Unitree G1 SDK.

## Test Infrastructure

### Test Helpers

All test scripts should use `g1_tests/robot_test_helpers.py` for common utilities:

```python
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2/g1_tests')
from robot_test_helpers import RobotTestConnection, simple_connect_robot

# Method 1: Context manager (auto-discovery and cleanup)
async with RobotTestConnection() as robot:
    # robot.ip, robot.mac, robot.mode available
    await robot.call_api(7001)  # Example API call

# Method 2: Simple connect (just get IP)
robot_ip = await simple_connect_robot()
```

### Discovery Testing

Test robot discovery functionality:

```bash
# Monitor discovery state changes in real-time
cd g1_tests && python3 test_discovery_monitor.py

# Test centralized discovery API
python3 -c "from g1_app.utils.robot_discovery import discover_robot; import asyncio; print(asyncio.run(discover_robot()))"
```

Expected output: `{'ip': '192.168.86.2', 'mac': 'fc:23:cd:92:60:02', 'mode': 'STA-L', 'online': True}`

## Test Categories

### Unit Tests

Test individual components in isolation:

```python
# Example: Test FSM state validation
def test_fsm_validation():
    from g1_app.core.fsm_validator import is_gesture_allowed
    
    assert is_gesture_allowed(fsm_id=500, mode=0) == True
    assert is_gesture_allowed(fsm_id=100, mode=0) == False
```

### Integration Tests

Test components working together:

```bash
# Test SLAM relocation
cd g1_tests && python3 test_relocation_detection.py

# Test map building with joystick
cd g1_tests && python3 test_map_build_with_joystick.py

# Test SLAM topics real-time
cd g1_tests && python3 test_slam_topics_realtime.py
```

### API Tests

Test specific robot APIs:

```bash
# Test heading API (1102)
cd g1_tests && python3 test_api_1102_heading.py

# Test custom actions
cd g1_tests && python3 test_custom_actions.py
```

## Writing New Tests

### Test Script Template

```python
#!/usr/bin/env python3
"""
Test: <Brief description>
Purpose: <What this validates>
"""
import asyncio
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2/g1_tests')
from robot_test_helpers import RobotTestConnection

async def main():
    async with RobotTestConnection() as robot:
        print(f"Testing with robot at {robot.ip}")
        
        # Your test code here
        result = await robot.call_api(7001)  # Example
        
        assert result is not None, "Test failed"
        print("✅ Test passed")

if __name__ == "__main__":
    asyncio.run(main())
```

### Best Practices

1. **Always use RobotTestConnection** - Don't hardcode IPs
2. **Test robot state first** - Verify FSM mode before sending commands
3. **Clean up after tests** - Return robot to safe state (DAMP mode)
4. **Add timeouts** - Don't let tests hang forever
5. **Document expected behavior** - What should happen if test passes?

## Running Test Suites

### Quick Test (Network Connectivity)

```bash
./quick_test.sh
```

Tests:
- Robot discovery via multicast
- Robot discovery via ARP
- Network mode detection
- Basic API call (GetFSMMode)

### DDS Diagnostic (EDU Models Only)

```bash
./diagnose_dds.sh
```

Tests:
- DDS environment variables
- DDS topic discovery
- CycloneDDS configuration

**Note**: G1 Air models don't use DDS - these tests will fail (expected).

### SLAM Test Suite

```bash
# Run all SLAM tests
./data/test_data/maps/run_all_tests.sh  # If exists

# Or manually:
python3 test_slam_topics_realtime.py
python3 test_relocation_detection.py
python3 test_map_build_with_joystick.py
```

## Test Monitoring

### Discovery Monitor

Monitor robot online/offline state changes:

```bash
cd g1_tests && python3 test_discovery_monitor.py
```

Output shows:
- Current state (online/offline)
- State changes with timestamps
- Time elapsed between changes
- Network mode and IP address

### SLAM Status Monitor

Monitor SLAM topics in real-time:

```bash
cd g1_tests && python3 test_slam_topics_realtime.py
```

Shows:
- Map updates
- Robot pose
- Navigation status
- LiDAR data

## Debugging Failed Tests

### Robot Not Found

```bash
# Check web server discovery
curl http://localhost:3000/api/discover

# Test centralized discovery directly
python3 -c "from g1_app.utils.robot_discovery import discover_robot; import asyncio; print(asyncio.run(discover_robot()))"
```

### API Call Failures

1. Check FSM state: `curl http://localhost:3000/api/state/fsm`
2. Verify robot mode (DAMP, START, etc.)
3. Check if service is running (ai_sport, g1_arm_example)
4. Look for error codes in response

### Timeout Issues

- Increase timeout in test: `robot.set_timeout(30)`
- Check network latency: `ping <robot_ip>`
- Verify robot isn't processing other commands

## Test Data

### Mock Data

For tests that don't need real robot:

```python
# Use mock relocation data
cd g1_tests && python3 test_relocation_detection_mock.py
```

### Test Maps

Sample maps in `data/test_data/maps/` directory:
- `test_room.pgm` - Small test room
- `large_space.pgm` - Larger area for navigation tests

## Performance Testing

### Discovery Performance

Expected timings (from live testing):
- Offline detection: ~49 seconds
- Online detection: ~97 seconds (includes 30s boot time)
- Scan interval: 2 seconds
- Missed scan tolerance: 1 scan

### API Response Times

Typical response times:
- GetFSMMode (7001): <100ms
- ExecuteCustomAction (7108): <200ms
- SLAM relocation (1102): 2-5 seconds

## CI/CD Integration

### Pre-Commit Tests

Run before each commit:

```bash
# Quick connectivity check
./quick_test.sh

# Verify centralized discovery
python3 -c "from g1_app.utils.robot_discovery import discover_robot; import asyncio; print(asyncio.run(discover_robot()))"
```

### Nightly Tests

Run comprehensive suite overnight:
- All SLAM tests
- All API tests
- Long-running stability tests
- Performance benchmarks

## See Also

- [Robot Discovery API](../api/robot-discovery.md) - Discovery testing details
- [SLAM Navigation Guide](slam-navigation.md) - SLAM-specific testing
- [Project Structure](../reference/project-structure.md) - Where test files live
