# Unitree SDK2 Development Guide

## 📚 Documentation

**IMPORTANT**: All documentation is now centralized in `/docs/README.md`. Always start there.

### Quick Links
- **[Main Documentation Index](../docs/README.md)** - Start here for all topics
- **[Robot Discovery API](../docs/api/robot-discovery.md)** - How to find robots (SINGLE SOURCE OF TRUTH)
- **[SLAM Navigation Guide](../docs/guides/slam-navigation.md)** - Mapping and waypoints
- **[Web Controller Guide](../g1_app/ui/WEB_UI_GUIDE.md)** - Browser-based control

### For AI Agents
1. Read `/docs/README.md` first
2. Check `/docs/api/` for API references
3. Check `/docs/guides/` for how-to guides  
4. Archived docs are in `/docs/archived/` (DO NOT USE for new code)

## ⚠️ CRITICAL SAFETY RULE ⚠️

**NEVER automatically send robot state-changing commands (FSM states, DAMP mode, balance mode, torque commands) without explicit user confirmation.**

- ❌ NO automatic DAMP mode entry
- ❌ NO automatic FSM state transitions
- ❌ NO automatic balance mode changes
- ❌ NO automatic zero-torque commands
- ✅ ONLY allow recording API calls (7109-7111)
- ✅ REQUIRE user confirmation dialog before ANY state change
- ✅ USER controls all robot state via main UI buttons

Violating this rule can cause physical injury. Always err on the side of requiring manual confirmation.

## Project Context

**Target Robot**: G1 Air (no secondary development capabilities)
**Current State**: 
- Robot works with Android app (control + status + video streaming)
- Robot works with R3-1 remote control
- Robot name: G1_6937, IP: 192.168.86.3
**Goal**: Replicate Android app functionality on Linux PC using this SDK

The G1 Air lacks secondary development mode, meaning you cannot run custom code on the robot itself. All control must happen over the network via DDS, similar to how the Android app operates.

**CRITICAL**: G1 Air models without Jetson Orin NX may have **limited or no SDK/DDS access**. The Android app may use a proprietary protocol instead of DDS. If you cannot receive DDS messages on native Ubuntu, your G1 Air likely doesn't broadcast DDS topics.

**Verified Findings (G1_6937 example):**
- Android app works (control + status + video) ✓
- R3-1 remote control works ✓
- Can ping robot on network ✓
- Zero DDS packets on ports 7400-7430 ✗
- No "Developer Mode" or "SDK Mode" in app or remote ✗
- Result: **G1 Air lacks SDK/DDS capability**

**WebRTC Topic Naming Convention (G1 Air):**
- WebRTC only publishes **low-frequency (lf) variants** of topics
- Standard topic: `rt/lowstate` → WebRTC topic: `rt/lf/lowstate`
- Pattern applies to all state topics: `rt/lf/sportmodestate`, `rt/lf/bmsstate`, etc.
- High-frequency DDS topics (used in SDK examples) are NOT available over WebRTC
- Always use `rt/lf/` prefix when subscribing to robot state over WebRTC

### WiFi Connection Modes

The G1 supports two WiFi modes (see [Unitree FAQ](https://support.unitree.com/home/en/G1_developer/FAQ)):

- **AP Mode**: Robot creates its own WiFi network (MyAccessPoint)
- **STA Mode** (Station): Robot connects to your existing WiFi network

When the app shows "[STA-T] device not online", the robot is configured for STA mode but not connected to your network. When connected (green indicator), you can proceed. You need to:
1. Connect both robot and PC to the same WiFi network
2. Find robot's IP address (check your router's DHCP leases or the Unitree app)
   - Example: G1_6937 → 192.168.86.3
   - EDU models with NX: Default might be `192.168.123.164`
3. Ensure UDP ports 7400-7430 are open for DDS discovery

## Architecture Overview

This SDK enables control of Unitree robots (G1, GO2, H1, A2, B2, B2W, GO2W) via **DDS (Data Distribution Service)** using Eclipse CycloneDDS. The core architecture separates **high-level API clients** (locomotion, arm control, audio) from **low-level DDS topics** (direct motor commands/state).

### System Architecture Diagram

![G1 SDK Architecture](g1_sdk_architecture.png)

The G1 system consists of multiple interconnected components:

**1. Cloud Service Layer** (Optional, requires user authorization)
- **Unitree Robotics Management Platform**: Cloud-based robot fleet management
  - **mqtt Server**: Message broker for cloud communication
  - **turn/stun Service**: WebRTC NAT traversal for remote video streaming
  - **HTTP Web API**: RESTful API for robot control and monitoring

**2. G1 Robot (PC1) - Primary Computer**
- **GTA Management Module**: Gateway management and coordination
- **BLE Network Module**: Bluetooth Low Energy for mobile app pairing
- **WebRTC Module**: Real-time video/audio streaming to mobile apps
- **DDS Data Middleware**: Central message bus for all robot components
  - **Basic Services**: Core robot functionality
  - **LIDAR Point Cloud**: 3D environment sensing
  - **Motion Control**: FSM, locomotion, balance control
  - **Functional Modules**: Advanced capabilities (obstacle avoidance, speech recognition, etc.)
  - **Multimedia Services**: Camera, audio, video processing
- **Executive Mechanism and Sensors**: Hardware interface layer (motors, IMU, cameras, etc.)

**3. Secondary Computer (PC2)** - Optional development computer
- **Switch**: Network bridge between PC1 and PC2
- **DDS SDK**: Direct DDS communication (what this SDK uses)
- **ROS2 SDK**: ROS2 bridge for ROS ecosystem integration
- **GST SDK**: GStreamer for advanced multimedia processing

**4. Unitree Explore App** (Mobile Application)
- **USER Interface**: Control, monitoring, and configuration
- **Remote WebRTC Signaling**: Cloud-mediated WebRTC connection setup
- **WebRTC Module**: Direct video/audio streaming from robot
- **BLE Module**: Initial pairing and network configuration (AP/STA mode switching)

**5. External Development Board/PC** (Your Development Environment)
- **DDS SDK**: Network-based DDS communication (requires EDU model with Jetson NX)
- **ROS2 SDK**: Optional ROS2 bridge
- **GST SDK**: Optional multimedia processing

### Communication Paths

- **DDS Data** (solid blue): Primary robot state and control (rt/lowstate, rt/lowcmd, etc.) - **EDU models only**
- **WebRTC Data Communication** (solid red): Video/audio streaming and control to mobile app - **G1 Air uses this**
- **Other DDS Communication** (dotted purple): Inter-module DDS messages
- **MQTT Publishing Subscription** (dotted line with arrows): Cloud sync
- **HTTP Data** (dotted): REST API calls for control commands - **G1 Air uses this**
- **Bluetooth BLE Data** (dotted): Initial pairing and WiFi configuration only (AP/STA mode switching)
- **Serial Communication** (chain line): Hardware interfaces

### Key Components

- **Robot-specific APIs**: Each robot has dedicated namespaces (`unitree::robot::g1`, `go2`, `h1`, etc.) with high-level clients (`LocoClient`, `SportClient`, `ArmActionClient`)
- **DDS Communication**: All robot communication uses publish/subscribe over DDS topics (e.g., `rt/lowstate`, `rt/lowcmd`) - **EDU models with Jetson NX only**
- **IDL Messages**: Auto-generated message types in `include/unitree/idl/{robot}/` from IDL definitions
- **ChannelFactory Pattern**: Centralized DDS initialization via singleton `ChannelFactory::Instance()->Init(domain_id, network_interface)`

### Your G1 Air Development Environment (Current Web Controller Project)

**IMPORTANT**: The G1 Air model uses the **Unitree Explore App architecture** (WebRTC + HTTP), **NOT** direct DDS SDK access. Your web-based controller project is **emulating the mobile app's behavior**.

**Critical Architecture Understanding:**
- **WebRTC is a wrapper around DDS**: The mobile app uses WebRTC to tunnel DDS communication through the robot's PC1
- **DDS runs internally on PC1**: The robot's onboard computer uses DDS for all internal modules
- **External access via WebRTC/HTTP**: Mobile app and your web controller access DDS indirectly through WebRTC/HTTP gateway on PC1

**Architecture Pattern (Matching Unitree Explore App):**
- **Communication protocol**: WebRTC for video + HTTP/WebSocket for control (wrapping DDS internally)
- **BLE usage**: Only for initial pairing and network configuration (AP/STA mode switching)
- **Network connection**: WiFi to robot's onboard PC1 (after BLE configures network)
- **No direct DDS access**: G1 Air models without Jetson Orin NX do not expose DDS topics externally
- **No SSH/direct access**: Cannot access robot's internal PC (no PC2 capability)

**Your Web Controller Implementation:**
- Replicates the **Unitree Explore App** functionality over web instead of mobile
- Uses same communication pattern: WebRTC/HTTP/WebSocket instead of DDS SDK
- BLE not needed (assumes robot already configured and on WiFi network)
- This explains why DDS discovery fails on G1 Air - it's simply not enabled on this model
- The robot responds to WebRTC signaling and HTTP commands, not DDS publish/subscribe

**Why DDS SDK Won't Work on G1 Air:**
- G1 Air lacks Jetson Orin NX (no PC2)
- No DDS middleware exposed externally
- Mobile app uses proprietary WebRTC/HTTP protocol
- SDK documentation is for EDU models only

### 3. Video Streaming
According to the scraped SDK documentation, video should be available via WebRTC module on PC1. The mobile app accesses this directly.

For reference, check GO2's video pattern in [example/go2/go2_video_client.cpp](example/go2/go2_video_client.cpp) - however, this requires DDS access (EDU only).

### 4. Status Information Display
The SDK documentation reveals key topics and APIs:

**From robot-state-client-interface.md:**
- Service names: `ai_sport` (main motion), `g1_arm_example` (arm service), `vui_service` (audio/lighting)
- Service switch API for enabling/disabling services

**From sport-services-interface.md:**
- LocoClient RPC interface for movement: `Move(vx, vy, vyaw)`, `StopMove()`, `Damp()`, `Start()`, `StandUp()`
- APIs match our constants: GET_FSM_ID (7001), GET_FSM_MODE (7002), SET_FSM_ID (7101), SET_VELOCITY (7105)

**From arm-action-interface.md:**
- ExecuteAction(action_id) for preset gestures (IDs 99, 11-27)
- ExecuteAction(action_name) for custom taught actions - **matches our implementation**
- StopCustomAction() for emergency stop
- Error codes: 7400 (occupied), 7401 (arm raised), 7404 (invalid FSM)

**Current Implementation Status:**
✅ Our code correctly implements ExecuteCustomAction API (7108) and StopCustomAction (7113)
✅ FSM validation logic matches SDK requirement: gestures only in states 500/501, or 801 with mode 0/3
✅ Battery monitoring via rt/lf/bms topic matches DDS pattern (though accessed via WebRTC wrapper)
⚠️ Need to verify service status monitoring (ServiceSwitch API from RobotStateClient)

### 5. Building a PC Controller - Current Implementation Review

**Architecture Alignment:**
Our web controller correctly replicates the Unitree Explore App architecture:
- ✅ WebRTC connection for video/control channel
- ✅ HTTP REST API for commands (movement, gestures)
- ✅ WebSocket for real-time state updates
- ✅ FSM state tracking via sportmodestate topic
- ✅ Battery monitoring via rt/lf/bms topic
- ✅ Gesture execution with FSM validation

**SDK Compliance:**
According to scraped documentation, our implementation:
- ✅ Correctly uses API IDs: 7108 (ExecuteCustomAction), 7113 (StopCustomAction), 7105 (SetVelocity), 7101 (SetFSMState)
- ✅ FSM state transitions match SDK state machine (ZERO_TORQUE → DAMP → START → LOCK_STAND/RUN)
- ✅ Gesture validation matches SDK error 7404 logic (fsm_id ∈ {500, 501} or {801 with mode ∈ {0, 3}})
- ✅ Topic subscriptions follow DDS naming: rt/lf/sportmodestate, rt/lf/bms
- ⚠️ Missing: Service status monitoring (RobotStateClient.ServiceSwitch)

**Recommended Improvements:**
1. Add service status monitoring via RobotStateClient interface
2. Implement action list retrieval (API 7107) to show available gestures
3. Add swing height control (GET_SWING_HEIGHT 7004, SET_SWING_HEIGHT 7103)
4. Add stand height control (GET_STAND_HEIGHT 7005, SET_STAND_HEIGHT 7104)
5. Consider balance mode control (GET_BALANCE_MODE 7003, SET_BALANCE_MODE 7102)

## Critical Setup Requirements

### Environment Variables (MANDATORY)
```bash
export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml  # DDS configuration
export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/{x86_64|aarch64}:$LD_LIBRARY_PATH
```
**Every executable** requires these - DDS won't discover robots without `CYCLONEDDS_URI` pointing to [cyclonedds.xml](cyclonedds.xml).

### Build System
- Architecture-specific prebuilt libraries in `lib/{x86_64,aarch64}/`
- CMake detects architecture via `CMAKE_SYSTEM_PROCESSOR` and links appropriate binary
- Third-party dependencies (CycloneDDS, yaml-cpp, Boost) in `thirdparty/`
- Conditional compilation: Some examples only build if dependencies found (see [example/g1/CMakeLists.txt](example/g1/CMakeLists.txt#L19-L26) for Boost/yaml-cpp checks)

## Code Patterns

### Client Initialization Pattern
```cpp
// 1. Initialize channel factory with network interface
unitree::robot::ChannelFactory::Instance()->Init(0, "eth0");  // domain_id=0

// 2. Create and initialize client
unitree::robot::g1::LocoClient client;
client.Init();           // Registers API endpoints
client.SetTimeout(10.f); // Configure timeout

// 3. Make API calls
int fsm_mode;
client.GetFsmMode(fsm_mode);  // Returns error code
```

### Low-Level DDS Pattern (Direct Motor Control)
```cpp
// Publisher for commands
ChannelPublisher<unitree_hg::msg::dds_::LowCmd_> cmd_pub("rt/lowcmd");
cmd_pub.InitChannel();

// Subscriber for state
ChannelSubscriber<unitree_hg::msg::dds_::LowState_> state_sub("rt/lowstate");
state_sub.InitChannel([](const void* msg) {
    auto* state = (const unitree_hg::msg::dds_::LowState_*)msg;
    // Process state
});

// Command loop
unitree_hg::msg::dds_::LowCmd_ cmd{};
cmd.motor_cmd()[0].q() = target_pos;      // Position
cmd.motor_cmd()[0].kp() = 50.0;           // Stiffness
cmd.motor_cmd()[0].kd() = 5.0;            // Damping
cmd_pub.Write(cmd);
```

### Motor Safety Pattern (G1 Specific)
See [example/g1/low_level/g1_dual_arm_example.cpp](example/g1/low_level/g1_dual_arm_example.cpp#L66-L85) for motor type-specific torque limits:
- GearboxS: ±17 Nm, GearboxM: ±82 Nm, GearboxL: ±200 Nm
- Always apply smooth position interpolation and torque clipping

## Robot-Specific Details

### G1 Humanoid
- **29 motors**: 12 leg, 3 waist, 14 arm (7 DOF per arm)
- **High-level**: `g1::LocoClient` (locomotion), `g1::G1ArmActionClient` (pre-programmed arm actions), `g1::AudioClient` (TTS/ASR)
- **Low-level topics**: `rt/lowstate` (state), `rt/lowcmd` (commands), `rt/utlidar/*` (LiDAR)
- **Service modes**: Must switch to appropriate mode (`sport_mode`, `ai_sport`, `advanced_sport`) via `MotionSwitcherClient` before low-level control

### GO2/B2 Quadrupeds
- **12 motors**: FR, FL, RR, RL legs (hip/thigh/calf per leg)
- **High-level**: `go2::SportClient` with APIs for gaits (`Move`, `SwitchGait`), tricks (`Hello`, `Stretch`, `FrontFlip`)
- **Service**: `robot_state` for mode switching, `config` for persistent settings
- Joint indices defined in [include/unitree/dds_wrapper/robots/go2/defines.h](include/unitree/dds_wrapper/robots/go2/defines.h#L15-L27)

### H1 Humanoid
- **20 motors**: 12 leg, 1 waist, 7 arm
- Similar to G1 but different joint layout - see [example/h1/low_level/motors.hpp](example/h1/low_level/motors.hpp#L19-L42)

## Common Issues & Solutions

### "[STA-T] device not online" in Android App
This means the robot is in STA (Station) mode but not connected to WiFi:
1. **Configure robot WiFi**: If you have NX access (EDU version), connect via UART/SSH and use `nmcli`:
   ```bash
   nmcli device wifi connect <SSID> password <password>
   ```
2. **Use AP mode instead**: Have robot create its own WiFi network (requires NX access)
3. **Check network**: Both PC and robot must be on same WiFi, verify with `ping <robot_ip>`

### Robot Not Broadcasting DDS (G1 Air Issue)
If you can ping the robot but receive no DDS messages on **native Ubuntu**:

**Control Methods Available:**
- ✓ Android app works (WiFi)
- ✓ R3-1 remote control works (likely 2.4GHz radio)
- ✗ SDK/DDS not working (needs investigation)

This suggests the robot is functional but SDK interface may need enabling:

1. **Check robot model**: G1 Air without NX may not support SDK/DDS at all
   - Look for Jetson Orin NX in the robot's back (EDU models have this)
   - Check robot firmware version in app - older versions may lack SDK support
2. **Enable SDK mode in app**: Some firmware versions require enabling developer mode
   - Look for "Developer Mode", "SDK Mode", or "Advanced Settings" in Unitree app
   - May require firmware update to latest version
   - R3-1 remote may have mode button to enable SDK mode
3. **Verify robot is actually broadcasting**: Use Wireshark to capture all UDP traffic:
   ```bash
   sudo tcpdump -i eth1 -n 'udp and (portrange 7400-7430)' -v
   ```
   If you see NOTHING when robot is powered on, it's not broadcasting DDS
4. **Android app may use different protocol**: Capture app traffic to see what it actually uses:
   ```bash
   sudo tcpdump -i eth1 host 192.168.86.3 -w capture.pcap
   # Use Android app while capturing
   wireshark capture.pcap  # Analyze what ports/protocols the app uses
   ```
5. **R3-1 remote control considerations**:
   - R3-1 uses direct radio connection (not WiFi/DDS)
   - Check if R3-1 has "SDK mode" or "Developer mode" button sequence
   - Some Unitree robots require R3-1 to enable SDK before DDS works

### No DDS Messages Received
**CRITICAL**: If you have a G1 Air model, DDS will **never work** - this is expected behavior. The G1 Air uses WebRTC/BLE (like the mobile app), not DDS. Skip DDS troubleshooting and focus on replicating the Unitree Explore App's WebRTC/BLE protocol instead.

For EDU models with Jetson NX that should support DDS:
1. **WSL2 Configuration**: WSL2 can work with DDS but requires proper setup:
   - **Check network mode**: WSL2 mirrored networking (Windows 11 22H2+) works best
   - **Verify interface**: Use interface that matches your Windows adapter (use `ip a`)
   - **CycloneDDS config**: May need to specify interface explicitly in cyclonedds.xml
   - **Try different interfaces**: Test with all available interfaces (eth0, eth1, wlan0)
2. Check `CYCLONEDDS_URI` points to valid [cyclonedds.xml](cyclonedds.xml)
3. Verify network interface name (use `ip a` to find `eth0`, `wlan0`, `eth1`, etc.)
4. Firewall must allow UDP ports 7400-7430 (DDS discovery)
5. Check if robot SDK mode is enabled in Unitree app settings

### Error 3104 or Timeout
- Robot not in correct mode - use Unitree app to enable SDK control
- MotionSwitcherClient may need to switch service mode first (see [example/g1/low_level/g1_dual_arm_example.cpp](example/g1/low_level/g1_dual_arm_example.cpp#L354-L367))

### Build Failures
- Missing dependencies: Install via `apt-get install cmake g++ libyaml-cpp-dev libeigen3-dev libboost-all-dev`
- Wrong architecture libraries: Verify `CMAKE_SYSTEM_PROCESSOR` matches available libs in `lib/`

## Testing Workflows

```bash
# Comprehensive DDS diagnostic (RECOMMENDED FIRST)
./diagnose_dds.sh  # Step-by-step connectivity test

# Quick connectivity test
./quick_test.sh  # Interactive test with robot

# Manual DDS test (if diagnostic passes)
export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml
export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH
./build/bin/test_subscriber  # Should show DDS topics

# Run robot tests (from g1_tests directory)
cd g1_tests
python3 test_slam_topics_realtime.py
python3 test_relocation_detection.py

# Capture Android app traffic to reverse-engineer protocol
./capture_robot_traffic.sh  # Run while using Android app
```

## Replicating Android App Functionality (G1 Air) - Current Project

**CRITICAL UNDERSTANDING**: The G1 Air uses **WebRTC + HTTP protocol**, NOT DDS. Your web controller project is emulating the Unitree Explore App's architecture, which bypasses the DDS SDK entirely.

### 1. Network Discovery & Traffic Analysis

**CRITICAL: NEVER hardcode robot IP addresses - discovery must be fully dynamic**

The Android app discovers robots without knowing their IP addresses beforehand.

**Primary Discovery Method - Scapy-based ARP Scanning (RECOMMENDED):**
```python
from g1_app.utils.robot_discovery import discover_robot

# Pure Python, no sudo required, <5 seconds
robot = discover_robot(target_mac="fc:23:cd:92:60:02")
if robot and robot['online']:
    print(f"Robot at {robot['ip']}")
```

**Technology**: 
- Uses Python `scapy` library for ARP scanning
- No external tools (no nmap, no arp-scan)
- No sudo/root permissions needed
- Cross-platform (Linux, Windows, macOS)
- Optimized: eth1 only, /24 subnet for large networks, <5 second discovery

**Manual Discovery Methods (for debugging only):**
```bash
# Method 1: ARP cache lookup (fastest)
arp -n | grep -i 'fc:23:cd:92:60:02'

# Method 2: Network scan with arp-scan (requires sudo)
sudo arp-scan -I eth1 --localnet | grep -i 'fc:23:cd:92:60:02'

# Method 3: nmap with MAC filtering (requires sudo, slow)
sudo nmap -sn 192.168.86.0/24 | grep -B 2 'FC:23:CD:92:60:02'
```

**Discovery Protocol Investigation:**
```bash
# Capture discovery traffic (NO IP specified - capture all broadcast/multicast)
sudo tcpdump -i eth1 '(broadcast or multicast)' -w discovery.pcap

# Listen for robot broadcasts
sudo tcpdump -i eth1 'udp and (dst 231.1.1.2 or dst 239.255.255.250 or broadcast)' -v

# Check SSDP discovery (UPnP)
sudo tcpdump -i eth1 'udp port 1900' -v
```

**After Robot is Discovered:**
- **WebRTC**: STUN/TURN traffic, DTLS handshakes for encrypted media (video streaming)
- **HTTP/WebSocket**: Control commands and signaling (movement, gestures, status)
- **BLE**: Only during initial pairing to configure WiFi (AP vs STA mode)
- **NO DDS traffic**: Ports 7400-7430 will be silent

### 2. Control Path (Web Controller Implementation)
Your current web-based controller replicates the mobile app using:
- **WebRTC**: For video streaming (robot camera to web browser)
- **HTTP REST API**: For command/control similar to app buttons (gestures, movement)
- **WebSocket**: For real-time state updates (battery, FSM mode, IMU data)
- **NO DDS SDK**: Direct robot control without DDS middleware
- **NO BLE**: Assumes robot already configured and connected to WiFi network

This is why your current implementation works (web server + robot state monitoring) while DDS SDK examples fail.

### 3. Known SDK Findings (From Scraped Documentation)

**Key Insights:**
1. **WebRTC wraps DDS internally**: The mobile app uses WebRTC to access DDS topics on PC1, not direct DDS
2. **Service architecture**: Robot runs multiple services (ai_sport, g1_arm_example, vui_service) controllable via RobotStateClient
3. **FSM state machine**: SDK confirms gesture restriction logic we implemented (states 500/501 always OK, 801 requires mode 0/3)
4. **Custom actions**: SDK confirms ExecuteAction(string) for teach mode, non-blocking execution
5. **Error codes**: 7400 (occupied), 7401 (arm raised), 7404 (invalid FSM) match our implementation

**API Verification:**
From dds-services-interface.md and arm-action-interface.md:
- ✅ Our API IDs are correct (7108 ExecuteCustomAction, 7113 StopCustomAction)
- ✅ Our FSM validation logic matches SDK requirements
- ✅ Our topic subscriptions follow correct DDS naming conventions
- ✅ Our error handling matches documented error codes

**Implemented Features:**
- ✅ Custom action management (APIs 7107-7114): Record, play, rename, delete
- ✅ Action list retrieval (7107 GetActionList)
- ✅ Full teach mode interface at /teach endpoint

**Optional Enhancements:**
- Service status monitoring (RobotStateClient.ServiceSwitch API)
- Swing/stand height control (APIs 7004/7103, 7005/7104)
- Balance mode control (APIs 7003/7102)

### 4. Code Review Summary

**Current Implementation Assessment:**

**✅ Correctly Implemented:**
1. **Architecture**: WebRTC + HTTP/WebSocket (not direct DDS) - matches Unitree Explore App
2. **API usage**: Correct API IDs from SDK documentation
3. **FSM state tracking**: Using sportmodestate topic as documented
4. **Battery monitoring**: Using rt/lf/bms topic (BmsState message)
5. **Gesture validation**: Matches SDK error 7404 logic exactly
6. **Custom actions**: ExecuteAction(string) non-blocking, StopCustomAction() emergency stop
7. **State machine**: Correct transitions (ZERO_TORQUE → DAMP → START → LOCK_STAND/RUN)
8. **Audio control**: TTS, volume control, LED control via VuiClient Service (APIs 9001-9006)
9. **Speech recognition**: Subscribes to rt/audio_msg for ASR (speech-to-text)
10. **LiDAR support**: Subscribes to rt/utlidar/cloud_livox_mid360 for point cloud data
11. **Video streaming**: WebRTC video track available (handled by WebRTC connection)

**⚠️ Potential Issues:**
1. **No service health monitoring**: Not tracking if ai_sport/g1_arm_example services are running
2. **No action list**: Not showing available gestures (API 7107)
3. **Limited movement control**: Could add swing/stand height, balance mode
4. **Video display**: WebRTC video needs HTML5 video element integration in UI

**✅ No Pending Questions:**
All major architecture questions resolved:
- WebRTC is wrapper around DDS ✓
- BLE only for pairing/network config ✓
- Control happens via HTTP/WebSocket over WiFi ✓
- FSM validation logic confirmed by SDK ✓
- Custom actions API correctly implemented ✓
- Audio/TTS via VuiClient Service ✓
- Speech recognition via rt/audio_msg topic ✓
- LiDAR data via rt/utlidar topics ✓
- Video via WebRTC module ✓

### 3. Video Streaming
Check `go2::VideoClient` pattern in [example/go2/go2_video_client.cpp](example/go2/go2_video_client.cpp) - G1 likely uses similar DDS-based video topics. Look for:
- Topic names: `rt/video/*` or `camera/*`
- Compression: H.264/H.265 encoded frames over DDS
- Use `test_subscriber` to discover available video topics

### 4. Status Information Display
Subscribe to `rt/lowstate` for comprehensive robot state:
```cpp
ChannelSubscriber<unitree_hg::msg::dds_::LowState_> state_sub("rt/lowstate");
state_sub.InitChannel([](const void* msg) {
    auto* state = (const unitree_hg::msg::dds_::LowState_*)msg;
    // Access: battery, IMU, motor states, temperatures
    std::cout << "Battery: " << state->battery_state().battery_voltage() << "V\n";
});
```

See [example/g1/test_robot_listener.cpp](example/g1/test_robot_listener.cpp) for a minimal state monitoring example.

### 5. Building a PC Controller
Recommended approach:
1. Start with test scripts to verify each capability (movement, status, video)
2. Use `g1::LocoClient` + `g1::ArmActionClient` for high-level control matching app gestures
3. Create a GUI (Qt/GTK) or web interface (HTTP server with websocket for real-time updates)
4. Handle video decoding (FFmpeg/GStreamer for H.264 streams from DDS topics)

### 6. Known Limitations (G1 Air)
- **No NX/Jetson access**: Cannot SSH into robot or configure WiFi directly
- **Pre-configured network only**: Robot must already be configured for your WiFi network
- **May not support SDK/DDS**: G1 Air models without Jetson NX may have zero SDK support
  - If no DDS messages on native Ubuntu after testing all troubleshooting steps, your model likely lacks SDK capability
  - Android app may use proprietary protocol not documented in this SDK
  - Consider contacting Unitree support to confirm SDK compatibility for your specific model
- Cannot modify robot-side firmware or deploy custom code
- Check Unitree app settings for "SDK Mode" or "Developer Mode" toggle - may require firmware update

### 7. Alternative Approaches (If SDK/DDS Not Available)

If your robot doesn't support SDK/DDS, you have limited options:

**Option 1: Reverse-Engineer Android App Protocol**

**Using Wireshark on Windows (RECOMMENDED):**
1. Open Wireshark on Windows
2. Select your WiFi adapter (the one connected to robot's network)
3. Set capture filter: `host 192.168.86.3` (your robot's IP)
4. Start capture
5. Use Android app to control robot (walk, move arms, etc.)
6. Stop capture after 1-2 minutes
7. Analyze:
   - Statistics → Conversations to see which ports are used
   - Look for repeating patterns when you press same button
   - Follow TCP/UDP streams to see message content
   - Check if it's JSON, binary, protobuf, or custom format

**Using tcpdump on Linux:**
```bash
# Capture app traffic while controlling robot
./capture_android_protocol.sh
# Or manually:
sudo tcpdump -i eth1 host 192.168.86.3 -w app_traffic.pcap
# Use Android app during capture, then analyze:
wireshark app_traffic.pcap  # Look for:
# - Repeating patterns when you press buttons
# - Port numbers being used
# - Message structure (JSON, binary, protobuf, etc.)
# - Command/response sequences
```

Once you identify the protocol, implement a Python/C++ client that:
- Opens same ports as the app
- Sends same command structure
- Parses responses for status/video data

**Option 2: Contact Unitree Support**
- Email: support@unitree.com
- Provide robot serial number (G1_6937)
- Ask: "Does this G1 Air model support SDK/DDS access?"
- Request: Upgrade path to SDK-enabled model or firmware

**Option 3: Upgrade to EDU Model**
- G1 EDU models include Jetson Orin NX with full SDK support
- Provides SSH access, DDS topics, and development capabilities
- Check with Unitree about upgrade/trade-in options
```bash
# If robot is on your network, find it via DDS broadcast
export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml
timeout 5 ./build/bin/test_subscriber  # Look for messages

# Scan local network for robot (adjust subnet to your network)
nmap -sn 192.168.86.0/24  # Example: 192.168.86.3 for G1_6937

# Check your router's DHCP leases for "unitree" or "g1" devices
# Ping test once you have the IP
ping -c 3 192.168.86.3
```

## File Organization Conventions

- `example/{robot}/high_level/`: Client API usage (recommended for new code)
- `example/{robot}/low_level/`: Direct DDS motor control (advanced, safety-critical)
- `include/unitree/robot/{robot}/`: Client headers and API definitions
- `include/unitree/idl/{robot}/`: Auto-generated DDS message types (DO NOT EDIT)
- Scripts (`*.sh`): Always set environment variables before running binaries

## When Writing New Examples

1. Always initialize `ChannelFactory` with correct network interface
2. Use high-level clients when possible (`LocoClient`, `SportClient`) - they handle API versioning and error codes
3. For low-level control: Implement safety limits, smooth interpolation, and emergency stops
4. Thread safety: Use `DataBuffer` pattern (see [g1_dual_arm_example.cpp](example/g1/low_level/g1_dual_arm_example.cpp#L27-L46)) for shared state between DDS callbacks and control loops
5. Test with `timeout` command first to avoid runaway loops: `timeout 10 ./build/bin/your_example`
