# Unitree G1 Robot SDK & Controller

Complete SDK and web-based controller for Unitree G1 humanoid robot.

## 📚 Documentation

**Start here**: [docs/README.md](docs/README.md)

All documentation is now centralized in the `docs/` directory:
- **Quick Start**: [docs/quickstart/QUICKSTART.md](docs/quickstart/QUICKSTART.md)
- **API Reference**: [docs/api/](docs/api/)
- **Guides**: [docs/guides/](docs/guides/)
- **Examples**: [example/](example/)

## 🚀 Quick Start

### 1. Discover Your Robot
```python
from g1_app.utils.robot_discovery import discover_robot
robot = discover_robot()
print(f"Robot at {robot['ip']} - {robot['mode']}")
```

### 2. Start Web Controller
```bash
cd g1_app/ui
python3 web_server.py
# Open http://localhost:3000
```

### 3. Run Examples
```bash
# Test robot connection
python3 -c "from g1_app.utils.robot_discovery import discover_robot; print(discover_robot())"

# SLAM navigation
cd G1_tests && python3 test_slam_topics_realtime.py

# Custom gestures
cd G1_tests && python3 watch_gesture_simple.py
```

## 🎯 Features

- ✅ **Web-based Controller** - Full robot control via browser
- ✅ **Robot Discovery** - Automatic network detection (multicast + ARP)
- ✅ **SLAM Navigation** - Mapping, localization, waypoint navigation
- ✅ **Gesture Control** - Custom taught gestures and actions
- ✅ **Real-time Monitoring** - WebRTC video, sensors, status

## 📖 Documentation Structure

```
docs/
├── README.md              # Main documentation index
├── api/                   # API references
│   └── robot-discovery.md # Robot discovery API ⭐
├── guides/                # How-to guides
│   ├── slam-navigation.md
│   └── testing-guide.md
├── reference/             # Technical reference
├── quickstart/            # Getting started
└── archived/              # Old/deprecated docs
```

## 🔧 Development

### Prerequisites
- Python 3.8+
- Network access to G1 robot
- Ubuntu/Linux (WSL2 works)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt  # If available

# Test robot connection
python3 -c "from g1_app.utils.robot_discovery import discover_robot; print(discover_robot())"
```

### Project Structure
- `g1_app/` - Web controller and utilities
- `G1_tests/` - Test scripts and examples
- `docs/` - All documentation
- `example/` - Official SDK examples
- `unitree_docs/` - Official Unitree documentation

## 📝 Key Documentation

**Essential**:
- [Robot Discovery API](docs/api/robot-discovery.md) - Find and connect to robots
- [Web UI Guide](g1_app/ui/WEB_UI_GUIDE.md) - Use the web controller
- [SLAM Navigation](docs/guides/slam-navigation.md) - Mapping and navigation

**For Developers**:
- [Development Guide](g1_app/DEVELOPMENT_GUIDE.md) - Setup and architecture
- [Testing Guide](docs/guides/testing-guide.md) - Test infrastructure
- [Project Structure](docs/reference/project-structure.md) - Code organization

**Official Unitree**:
- [Unitree Docs Index](unitree_docs/INDEX.md) - Official SDK documentation
- [Architecture](unitree_docs/architecture-description.md) - System design
- [API Reference](unitree_docs/dds-services-interface.md) - DDS services

## 🤖 Robot Information

- **Model**: G1 Air (no secondary development mode)
- **Serial**: E21D1000PAHBMB06
- **MAC**: fc:23:cd:92:60:02
- **Communication**: WebRTC + HTTP (not DDS)
- **Network**: STA mode (connects to your WiFi)

## 🆘 Troubleshooting

**Robot not found?**
- Check WiFi connection (robot must be on same network)
- Verify with Android app first
- See [Troubleshooting Guide](docs/guides/troubleshooting.md)

**Discovery slow?**
- Normal: 2-4 seconds online detection, ~49 seconds offline detection
- See [Robot Discovery API](docs/api/robot-discovery.md)

**Need help?**
- Check [FAQ](docs/guides/faq.md)
- Search [docs/](docs/)
- Review [examples/](example/)

## 📄 License

See [LICENSE](LICENSE) for Unitree SDK license.

## 🔗 Links

- [Unitree Robotics](https://www.unitree.com/)
- [Official G1 Docs](https://support.unitree.com/home/en/G1_developer)
- [Support Forum](https://support.unitree.com/)

---

**Start here**: [docs/README.md](docs/README.md) | **Quick Start**: [docs/quickstart/QUICKSTART.md](docs/quickstart/QUICKSTART.md)
