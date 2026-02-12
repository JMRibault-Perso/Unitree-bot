# G1 Robot Documentation

**Last Updated**: February 8, 2026

This is the **SINGLE SOURCE OF TRUTH** for all G1 robot documentation. All agents (human and AI) should start here.

## 📚 Documentation Structure

```
docs/
├── README.md (this file)          # Main index
├── quickstart/                     # Getting started guides
├── api/                           # API references
├── guides/                        # How-to guides
├── reference/                     # Technical reference
└── archived/                      # Old/deprecated docs
```

## 🚀 Quick Start

**Dependencies**: Python 3.8+, scapy (for robot discovery)

```bash
pip3 install -r requirements.txt  # Installs scapy + FastAPI + other deps
```

**New to the project?** Start here:

1. **[Robot Discovery](api/robot-discovery.md)** - Find your robot on the network (scapy-based, <5s)
2. **[Web UI Guide](../g1_app/ui/WEB_UI_GUIDE.md)** - Use the web controller
3. **[Testing Guide](guides/testing-guide.md)** - Run test scripts

## 📖 Core Documentation

### Essential References
- **[Robot Discovery API](api/robot-discovery.md)** - How to find and connect to robots
- **[SLAM Navigation](guides/slam-navigation.md)** - Mapping and waypoint navigation
- **[Gesture Control](guides/gesture-control.md)** - Custom taught gestures
- **[Web Controller](../g1_app/README.md)** - Web-based robot control

### For Developers
- **[Development Setup](../g1_app/DEVELOPMENT_GUIDE.md)** - Environment setup
- **[Project Structure](reference/project-structure.md)** - Code organization
- **[Testing Infrastructure](guides/testing-guide.md)** - Test suite overview

### Official Unitree Docs
- **[Unitree SDK Docs](../unitree_docs/INDEX.md)** - Official documentation
- **[Architecture](../unitree_docs/architecture-description.md)** - System architecture
- **[API Reference](../unitree_docs/dds-services-interface.md)** - DDS services

## 🎯 Common Tasks

### Discover Robot
```python
from g1_app.utils.robot_discovery import discover_robot
robot = discover_robot()
if robot and robot['online']:
    print(f"Robot at {robot['ip']}")
```
📖 [Full API Documentation](api/robot-discovery.md)

### Start Web Controller
```bash
cd g1_app/ui
python3 web_server.py
# Open http://localhost:3000
```
📖 [Web UI Guide](../g1_app/ui/WEB_UI_GUIDE.md)

### Run SLAM Navigation
```bash
python3 test_slam_topics_realtime.py  # Test SLAM topics
python3 build_room_map.py            # Build a map
python3 G1_SLAM_IMPLEMENTATION.py    # Full navigation
```
📖 [SLAM Navigation Guide](guides/slam-navigation.md)

### Execute Custom Gesture
```python
from robot_test_helpers import RobotTestConnection
async with RobotTestConnection() as robot:
    await robot.execute_custom_action("wave")
```
📖 [Gesture Control Guide](guides/gesture-control.md)

## 📑 API Documentation

### Robot Discovery
- **[Robot Discovery](api/robot-discovery.md)** - `discover_robot()`, `wait_for_robot()`
- Technology: Scapy-based ARP scanning (pure Python, no sudo, cross-platform)
- Performance: <5 seconds on typical networks
- Status: ✅ Production-ready

### SLAM & Navigation
- **[SLAM Topics](api/slam-topics.md)** - Real-time positioning, mapping, obstacles
- **[Navigation APIs](api/navigation-apis.md)** - Waypoint navigation, map building
- Status: ✅ Production-ready

### Motion Control
- **[Gesture API](api/gesture-api.md)** - Custom taught gestures (teach mode)
- **[Movement API](api/movement-api.md)** - Velocity control, FSM states
- Status: ✅ Production-ready

## 🧪 Testing

### Test Suites
- **[Testing Guide](guides/testing-guide.md)** - Overview of test infrastructure
- **[SLAM Tests](guides/slam-testing.md)** - Navigation and mapping tests
- **[Robot Tests](../g1_tests/README.md)** - Motion and gesture tests

### Quick Tests
```bash
# Discover robot
python3 -c "from g1_app.utils.robot_discovery import discover_robot; print(discover_robot())"

# Test SLAM topics
cd g1_tests && python3 test_slam_topics_realtime.py

# Test gestures
cd g1_tests && python3 watch_gesture_simple.py
```

## 🗂️ Documentation Index

### By Topic

**Robot Discovery & Connection**
- [Robot Discovery API](api/robot-discovery.md) ⭐ **Start here**
- [Network Modes (AP/STA)](reference/network-modes.md)
- [WebRTC Protocol](reference/webrtc-protocol.md)

**SLAM & Navigation**
- [SLAM Navigation Guide](guides/slam-navigation.md)
- [SLAM Topics Reference](api/slam-topics.md)
- [Navigation APIs](api/navigation-apis.md)
- [Map Building](guides/map-building.md)
- [Waypoint Navigation](guides/waypoint-navigation.md)

**Motion & Control**
- [Gesture Control](guides/gesture-control.md)
- [Movement Control](api/movement-api.md)
- [FSM States](reference/fsm-states.md)

**Development**
- [Project Structure](reference/project-structure.md)
- [Code Standards](reference/code-standards.md)
- [Testing Guide](guides/testing-guide.md)

## 📦 Archived Documentation

Old documentation has been moved to `docs/archived/`. These are kept for historical reference:
- `ENHANCED_DISCOVERY_*.md` - Old discovery methods (superseded by [robot-discovery.md](api/robot-discovery.md))
- `SLAM_GOALS_*.md` - Old SLAM implementation notes
- Various `*_SUMMARY.md` - Implementation snapshots

See [Archived Docs Index](archived/README.md) for full list.

## 🔄 For AI Agents

**If you are an AI assistant working with this codebase:**

1. **Always start here**: Read this README first
2. **Use current docs**: Refer to files in `docs/` not root-level MD files
3. **Check deprecation**: If you see `DEPRECATED` in a file, find the replacement
4. **Single source of truth**: 
   - Robot discovery: [api/robot-discovery.md](api/robot-discovery.md)
   - SLAM: [guides/slam-navigation.md](guides/slam-navigation.md)
   - Web UI: [../g1_app/ui/WEB_UI_GUIDE.md](../g1_app/ui/WEB_UI_GUIDE.md)

5. **Update copilot instructions**: Main AI context is in `.github/copilot-instructions.md`

## 📝 Contributing

When adding new documentation:
1. Place in appropriate `docs/` subdirectory
2. Update this README's index
3. Link from related documents
4. Mark old docs as deprecated if replacing

## 🆘 Help & Support

- **Issues**: Check [Troubleshooting Guide](guides/troubleshooting.md)
- **Examples**: See [Examples Directory](../example/)
- **Tests**: See [g1_tests/](../g1_tests/)

---

**Questions?** Check the [FAQ](guides/faq.md) or search this documentation.

**Found outdated info?** Check [docs/archived/](archived/) or update it!
