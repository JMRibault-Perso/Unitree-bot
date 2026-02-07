# Installation and Setup

## Prerequisites

- Python 3.8+
- Linux system (tested on Ubuntu)
- Network access to G1 robot
- go2_webrtc_connect library (git submodule at `deps/go2_webrtc_connect`)

## Installation Steps

### 0. Pull External Dependencies

```bash
cd /path/to/your/repo

./scripts/pull_deps.sh
git submodule update --init --recursive
```

### 1. Install Python Dependencies

```bash
cd /path/to/your/repo

# Install required packages
pip3 install asyncio

# Optional: For advanced features
pip3 install numpy  # For LiDAR processing
pip3 install opencv-python  # For video processing
```

### 2. Configure Robot Connection

Create a `.env` file or export environment variables:

```bash
# Robot configuration
export G1_ROBOT_IP=192.168.86.16
export G1_ROBOT_SN=E21D1000PAHBMB06

# Optional: Sensor configuration
export G1_ENABLE_ODOM=true
export G1_ENABLE_LIDAR=true
export G1_ENABLE_VUI=true
export G1_ENABLE_VIDEO=true
```

Or edit the defaults in `g1_app/utils/config.py`.

### 3. Verify WebRTC Library

The application uses the go2_webrtc_connect library. Verify it's available:

```bash
python3 -c "import sys; sys.path.insert(0, './deps/go2_webrtc_connect'); import unitree_webrtc_connect; print('OK')"
```

### 4. Test Connection

Run the CLI test interface:

```bash
cd /path/to/your/repo
python3 -m g1_app.cli_test
```

You should see:
```
Connecting to G1 at 192.168.86.16...
✅ Connected to robot

G1 ROBOT CONTROLLER - CLI INTERFACE
==========================================
...
```

## Network Setup

### WiFi Connection

The robot must be on the same WiFi network as your PC:

1. **Check robot WiFi status** in Unitree app:
   - Should show "[STA] device online" (green)
   - Note the robot's IP address

2. **Verify connectivity**:
   ```bash
   ping 192.168.86.16  # Replace with your robot's IP
   ```

3. **Check WebRTC ports**:
   The go2_webrtc_connect library handles WebRTC negotiation automatically over WiFi.

### Troubleshooting Network Issues

If connection fails:

1. **Verify robot is powered on and WiFi connected**
   - LED should be lit (check color)
   - Android app should show "online"

2. **Check firewall**:
   ```bash
   # Allow WebRTC ports (if firewall enabled)
   sudo ufw allow 8080/tcp
   sudo ufw allow 8443/tcp
   ```

3. **Test with Android app first**:
   - Ensure robot works with official app
   - Verify you can see video stream
   - Check FSM state (should be Damp or Ready)

4. **Enable debug logging**:
   ```python
   from g1_app.utils import setup_app_logging
   setup_app_logging(verbose=True)
   ```

## Project Structure

After setup, your directory should look like:

```
/path/to/your/repo/
├── g1_controller.py          # Original test script
├── G1_AIR_CONTROL_GUIDE.md   # Discovery documentation
├── QUICK_REFERENCE.md         # Quick reference
├── g1_app/                   # Main application package
│   ├── __init__.py
│   ├── core/                 # Core modules
│   │   ├── __init__.py
│   │   ├── event_bus.py
│   │   ├── state_machine.py
│   │   ├── command_executor.py
│   │   └── robot_controller.py
│   ├── api/                  # API definitions
│   │   ├── __init__.py
│   │   └── constants.py
│   ├── sensors/              # Sensor managers
│   │   ├── __init__.py
│   │   ├── odometry_manager.py
│   │   ├── lidar_manager.py
│   │   ├── vui_manager.py
│   │   └── video_manager.py
│   ├── utils/                # Utilities
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logger.py
│   ├── cli_test.py           # CLI interface
│   ├── README.md             # Architecture overview
│   ├── DEVELOPMENT_GUIDE.md  # This guide
│   └── INSTALLATION.md       # Installation guide
├── deps/
│   ├── unitree_sdk2/            # External SDK (pulled)
│   ├── unitree_sdk2_python/     # External Python SDK (pulled)
│   └── go2_webrtc_connect/      # WebRTC library (pulled)
```

## Testing the Installation

### 1. Run Basic Tests

```bash
# Test imports
python3 -c "from g1_app import RobotController, EventBus, FSMState; print('Imports OK')"

# Test configuration
python3 -c "from g1_app.utils import config; print(config)"

# Test connection (robot must be on)
python3 << EOF
import asyncio
from g1_app import RobotController

async def test():
    controller = RobotController("192.168.86.16", "E21D1000PAHBMB06")
    try:
        await controller.connect()
        print("✅ Connection successful")
        state = controller.current_state
        print(f"Current state: {state.fsm_state.name}")
        await controller.disconnect()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.run(test())
EOF
```

### 2. Run CLI Interface

```bash
python3 -m g1_app.cli_test
```

Try commands:
- Press `i` to see current state
- Press `d` to go to Damp mode
- Press `r` to go to Ready mode
- Press `h` for help

### 3. Test Event System

```python
import asyncio
from g1_app import RobotController, EventBus, Events

async def test_events():
    controller = RobotController("192.168.86.16", "E21D1000PAHBMB06")
    
    # Subscribe to state changes
    def on_state(state):
        print(f"State changed: {state.fsm_state.name}")
    
    EventBus.subscribe(Events.STATE_CHANGED, on_state)
    
    # Connect and trigger state change
    await controller.connect()
    await controller.damp()
    await asyncio.sleep(2)
    await controller.ready()
    await asyncio.sleep(2)
    await controller.disconnect()

asyncio.run(test_events())
```

## Common Issues

### "ModuleNotFoundError: No module named 'unitree_webrtc_connect'"

The WebRTC library path may not be set. Fix:

```python
# Add to your scripts before imports:
import sys
sys.path.insert(0, './deps/go2_webrtc_connect')
```

Or set PYTHONPATH:
```bash
export PYTHONPATH=./deps/go2_webrtc_connect:$PYTHONPATH
```

### "Connection timeout" or "Failed to connect"

1. Verify robot is powered on and WiFi connected
2. Ping the robot: `ping 192.168.86.16`
3. Test with Android app first
4. Check robot serial number matches
5. Try resetting robot WiFi in app

### "State transition rejected"

Check the current FSM state and valid transitions:

```python
state = controller.current_state
print(f"Current: {state.fsm_state.name}")
allowed = controller.state_machine.get_allowed_transitions()
print(f"Can go to: {[s.name for s in allowed]}")
```

### Sensor data not received

1. Check sensor managers are enabled:
   ```python
   print(controller.odom_manager is not None)
   print(controller.lidar_manager is not None)
   ```

2. Subscribe to events with debug:
   ```python
   def debug(data):
       print(f"Received: {type(data)}")
   EventBus.subscribe(Events.ODOMETRY, debug)
   ```

3. Enable debug logging:
   ```python
   from g1_app.utils import setup_app_logging
   setup_app_logging(verbose=True)
   ```

## Next Steps

Once installation is verified:

1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for usage examples
2. Review [README.md](README.md) for architecture details
3. Explore [G1_AIR_CONTROL_GUIDE.md](../G1_AIR_CONTROL_GUIDE.md) for API details
4. Start building your application!

## Getting Help

If you encounter issues:

1. Check logs with verbose mode enabled
2. Review the troubleshooting section
3. Test basic connectivity with `ping` and Android app
4. Verify environment variables are set correctly
5. Check that all dependencies are installed

For API-specific questions, refer to:
- [Official Unitree Documentation](https://support.unitree.com/home/en/G1_developer)
- [G1 Air Control Guide](../G1_AIR_CONTROL_GUIDE.md)
