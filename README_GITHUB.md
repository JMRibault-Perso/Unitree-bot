# Unitree G1 Robot Control System

A comprehensive web-based control system for Unitree G1 robots with automatic discovery, FSM state management, and real-time monitoring capabilities.

![G1 Robot Controller](https://img.shields.io/badge/Robot-Unitree%20G1-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-red)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-yellow)

## 🚀 Features

### 🤖 Robot Discovery & Connection
- **Automatic Discovery**: Multi-layer robot detection via mDNS, multicast UDP, and ARP scanning
- **MAC-based Identification**: Persistent robot binding using hardware addresses
- **Real-time Status**: Live online/offline detection with ping monitoring
- **Dynamic IP Management**: Automatic IP address updates without persistent storage

### 🎮 Web-based Control Interface
- **Modern UI**: Clean, responsive web interface for robot control
- **FSM State Machine**: Visual state management with 12+ robot states
- **Real-time Updates**: WebSocket-based live status monitoring
- **Connection Management**: Easy connect/disconnect with status indicators

### 🔧 Advanced Features
- **DDS Communication**: Full Eclipse CycloneDX integration
- **Multi-protocol Support**: WebRTC, mDNS, UDP multicast discovery
- **Network Analysis**: Comprehensive PCAP capture and protocol analysis
- **Cross-platform**: Works on Linux, WSL2, and native Ubuntu

## 📋 Requirements

- Python 3.8+
- Ubuntu/Linux environment (WSL2 supported)
- Network access to robot's WiFi network
- Root privileges for network scanning

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JMRibault-Perso/Unitree-bot.git
   cd Unitree-bot
   ```

2. **Install dependencies**
   ```bash
   pip install fastapi uvicorn websockets subprocess32 asyncio zeroconf
   ```

3. **Set up environment**
   ```bash
   export CYCLONEDX_URI=file://$(pwd)/cyclonedds.xml
   export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH
   ```

4. **Build the SDK (if needed)**
   ```bash
   mkdir -p build && cd build
   cmake ..
   make -j$(nproc)
   cd ..
   ```

## 🚀 Quick Start

1. **Start the web server**
   ```bash
   cd g1_app
   python3 -m uvicorn ui.web_server:app --host 0.0.0.0 --port 8000
   ```

2. **Open web interface**
   - Navigate to `http://localhost:8000`
   - Wait for robot discovery (robots appear automatically)
   - Click "🔗 Connect" on your robot
   - Use FSM controls to manage robot state

3. **Alternative: Quick connect script**
   ```bash
   ./quick_test.sh
   ```

## 🔍 Robot Discovery Protocol

The system uses a multi-layer discovery approach:

### Layer 1: Multicast UDP Discovery
- **Address**: 231.1.1.2:10134
- **Protocol**: JSON broadcast messages
- **Format**: `{"sn": "serial", "name": "robot_name", "ip": "current_ip"}`

### Layer 2: mDNS Discovery
- **Service**: `_Unitree._tcp.local.`
- **Hostname**: `Unitree.local.`
- **Port**: 5353

### Layer 3: ARP Scanning
- **MAC Address**: fc:23:cd:92:60:02 (example)
- **Network**: Auto-detected subnet ranges
- **Fallback**: Manual IP ping testing

## 🎯 FSM State Management

The system manages 12 robot states:

| State | ID | Description |
|-------|----|----|
| `passive` | 0 | Safe startup state |
| `fixedStand` | 1 | Standing position |
| `freeStand` | 2 | Free standing mode |
| `sport` | 6 | Sport/walking mode |
| `walk` | 7 | Walking locomotion |
| `run` | 8 | Running gait |
| `climb` | 9 | Climbing mode |
| `damping` | 10 | Damping/compliance |
| `recovery` | 11 | Recovery operations |
| `backflip` | 12 | Backflip maneuver |
| `jumpYaw` | 13 | Jump with yaw |
| `straightHand` | 14 | Arm positioning |

## 🌐 Web API Endpoints

### Discovery
- `GET /api/discover` - List discovered robots
- `POST /api/connect?robot_name=X&ip=Y` - Connect to robot
- `POST /api/disconnect` - Disconnect from robot

### State Management  
- `GET /api/state` - Get current FSM state
- `POST /api/set_state?state_name=X` - Change FSM state
- `GET /api/transitions` - Get allowed transitions

### Monitoring
- `WebSocket /ws` - Real-time status updates
- `GET /api/status` - Robot connection status

## 🔧 Configuration

### Network Interface
Update network interface in discovery files:
```python
NETWORK_INTERFACE = "eth1"  # Change to your interface
```

### Robot Binding
Robots are automatically bound on first discovery. Remove bindings:
```bash
rm /tmp/unitree_robots.json
```

## 📊 Network Analysis

The project includes comprehensive network analysis tools:

### PCAP Capture
```bash
./capture_robot_traffic.sh  # Capture robot communications
./diagnose_dds.sh          # DDS diagnostics
```

### Protocol Analysis
- **WebRTC Discovery**: Port scanning and STUN analysis
- **DDS Topics**: Real-time topic monitoring  
- **Multicast Analysis**: UDP broadcast investigation

## 🐛 Troubleshooting

### Robot Not Discovered
1. Check robot is powered on and connected to same network
2. Verify network interface: `ip a`
3. Test connectivity: `ping <robot_ip>`
4. Run diagnostics: `./diagnose_dds.sh`

### Connection Issues
1. Ensure robot is in correct mode (not SDK mode)
2. Check firewall: `sudo ufw allow 7400:7430/udp`  
3. Verify DDS environment: `echo $CYCLONEDX_URI`
4. Test with simple script: `./quick_test.sh`

### WSL2 Issues
1. Use mirrored networking (Windows 11 22H2+)
2. Check interface mapping: `ip route show`
3. Test with different interfaces: `eth0`, `eth1`, `wlan0`

## 📁 Project Structure

```
├── g1_app/                 # Main application
│   ├── core/              # Robot discovery & connection
│   ├── ui/                # Web interface & API
│   └── robot/             # Robot control logic
├── example/               # SDK examples
├── include/               # C++ headers
├── lib/                   # Compiled libraries  
├── thirdparty/           # Dependencies
├── *.pcapng              # Network captures
├── *.sh                  # Shell scripts
└── *.md                  # Documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`  
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Unitree Robotics for the G1 platform
- Eclipse CycloneDX for DDS communication
- FastAPI and WebSocket communities

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check troubleshooting documentation
- Review network analysis guides

---

**Note**: This system is designed for the Unitree G1 Air model without secondary development capabilities. All control happens over the network via DDS, similar to the Android app operation.