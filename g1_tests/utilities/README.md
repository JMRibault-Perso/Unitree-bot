# Utility Scripts

Helper scripts for robot discovery, monitoring, and development tools.

## 🗂️ Available Scripts

### Discovery
- `discover_robot.py` - Auto-discover G1 via ARP (MAC: fc:23:cd:92:60:02)
- `list_services.py` - Query available robot services
- `list_topics.py` - List all WebRTC topics

### Monitoring
- `monitor_status.py` - Continuous robot status dashboard
- `watch_topics.py` - Real-time topic message viewer
- `sniff_webrtc.py` - WebRTC traffic analyzer

### Development
- `quick_connect.py` - Test WebRTC connection only
- `verify_connection.py` - Full connection diagnostic
- `show_available_actions.py` - Display all gesture actions

### Map Tools
- `slam_map_viewer.py` - Visualize saved maps
- `convert_map.py` - Convert between map formats

## 📝 Quick Commands

### Find Robot
```bash
python3 discover_robot.py
# Output: Found robot at 192.168.86.3
```

### List All Topics
```bash
python3 list_topics.py
```

### Monitor Robot Status
```bash
python3 monitor_status.py
# Shows: Battery, FSM state, position, velocities
```

### Verify Connection
```bash
python3 verify_connection.py
# Tests: ARP discovery, WebRTC connection, topic subscription
```

## 🔧 Helper Patterns

All utilities use standardized connection:

```python
from robot_test_helpers import RobotTestConnection

async with RobotTestConnection() as robot:
    # Auto discovers robot via ARP
    # Connects via WebRTC
    # Handles disconnect automatically
    pass
```

## 📚 Common Use Cases

### Daily Startup Check
```bash
python3 discover_robot.py  # Verify robot on network
python3 verify_connection.py  # Test full connection
python3 monitor_status.py  # Check robot health
```

### Before SLAM Testing
```bash
python3 list_topics.py | grep slam
python3 list_topics.py | grep lidar
```

### Debugging Gestures
```bash
python3 show_available_actions.py  # See all actions
python3 list_services.py  # Verify g1_arm_example running
```

## 🚨 Troubleshooting Tools

- **Connection issues**: Use `verify_connection.py`
- **Topic not found**: Use `list_topics.py`
- **Robot not discovered**: Use `discover_robot.py` with debug output
- **Service errors**: Use `list_services.py` to check service status
