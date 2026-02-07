# 📋 G1 Test Suite - Quick Reference

## 🏃 Quick Start

```bash
cd /path/to/your/repo/g1_tests
./run_all_tests.sh            # See all available tests
```

## 📍 Directory Guide

| Category | Path | Purpose |
|----------|------|---------|
| 🗺️  SLAM | `slam/` | Mapping, navigation, obstacle avoidance |
| 🤖 Motion | `motion/` | FSM control, movement, balance |
| 🦾 Arm | `arm/` | Teach mode, gestures, actions |
| 📡 Sensors | `sensors/` | LiDAR, cameras, telemetry |
| 🔧 Utilities | `utilities/` | Discovery, monitoring, debugging |

## ⚡ Most Used Commands

### Check Robot Status
```bash
cd utilities
./discover_robot.py          # Find robot IP
./monitor_telemetry.py       # Live status dashboard
```

### Control Robot
```bash
cd motion
./simple_control.py          # Interactive control (d/r/b/u/s/h)
```

### SLAM Navigation
```bash
cd slam
./start_mapping.py           # Start mapping
./save_map.py --name room    # Save map
./load_map.py --name room    # Load map
./test_navigation_v2.py --target-x 1.0 --target-y 0.0  # Navigate
./stop_slam_v2.py            # Stop SLAM
```

### Arm Control
```bash
cd arm
./list_actions.py            # Show available actions
./enable_teach_mode.py       # Enter teach mode
./enable_teach_mode.py --disable  # Exit teach mode
```

### Monitor Sensors
```bash
cd sensors
./listen_all.py              # Monitor all topics
./monitor_lidar.py           # LiDAR statistics
```

## 🎯 FSM State Sequence

```
ZERO_TORQUE (0)
    ↓
DAMP (1001) ← command 'd'
    ↓
READY (1005) ← command 'r'
    ↓
BALANCE_STAND (1002) ← command 'b'
STAND_UP (1004) ← command 'u'
SIT (1009) ← command 's'
HELLO (1016) ← command 'h'
```

**Always:** DAMP first, then READY, then motion commands

## 🗺️  SLAM API Quick Ref

| Command | API ID | Usage |
|---------|--------|-------|
| Start Mapping | 1801 | `./start_mapping.py` |
| Save Map | 1803 | `./save_map.py --name <name>` |
| Load Map | 1804 | `./load_map.py --name <name>` |
| Navigate | 1102 | `./test_navigation_v2.py --target-x X --target-y Y` |
| Pause Nav | 1201 | `./cancel_navigation_v2.py` |
| Close SLAM | 1901 | `./stop_slam_v2.py` |

## 🦾 Arm API Quick Ref

| Command | API ID | Usage |
|---------|--------|-------|
| List Actions | 7107 | `./list_actions.py` |
| Enable Teach | 7110 | `./enable_teach_mode.py` |
| Disable Teach | 7111 | `./enable_teach_mode.py --disable` |

## 📡 Common Topics

| Topic | Content |
|-------|---------|
| `rt/lf/sportmodestate` | Robot state, FSM, odometry |
| `rt/lf/bmsstate` | Battery status |
| `rt/utlidar/cloud_livox_mid360` | LiDAR point cloud |
| `rt/api/slam_operate/response` | SLAM responses |
| `rt/api/sport/response` | Motion responses |
| `rt/api/arm_action/response` | Arm action responses |

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Robot not found | `./utilities/discover_robot.py` |
| Connection fails | Check WiFi, verify `ping 192.168.86.3` |
| Import errors | Check `sys.path` includes parent dir |
| SLAM fails | Verify FSM state (needs DAMP/READY/RUN) |
| Gesture fails | Check FSM state (needs 500/501 or 801) |

## 📚 Full Documentation

- **Master Guide:** [`README.md`](README.md)
- **Standards:** [`../TEST_SCRIPT_STANDARDS.md`](../TEST_SCRIPT_STANDARDS.md)
- **Migration:** [`../MIGRATION_GUIDE.md`](../MIGRATION_GUIDE.md)
- **Complete Summary:** [`../TEST_SUITE_COMPLETE.md`](../TEST_SUITE_COMPLETE.md)
- **Category READMEs:** Check each subdirectory

## 💡 Pro Tips

1. **Always use context manager:**
   ```python
   async with RobotTestConnection() as robot:
       # Your code here
   ```

2. **Get help on any script:**
   ```bash
   python3 script.py --help
   ```

3. **Monitor during testing:**
   ```bash
   # Terminal 1: Run your test
   ./test_navigation_v2.py ...
   
   # Terminal 2: Monitor status
   cd ../utilities && ./monitor_telemetry.py
   ```

4. **Check available tests:**
   ```bash
    cd /path/to/your/repo/g1_tests
   ./run_all_tests.sh
   ```

---

**Made with ❤️  to eliminate daily bug rediscovery!**
