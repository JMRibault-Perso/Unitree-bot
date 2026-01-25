# Unitree SDK2 Development Guide

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

### Key Components

- **Robot-specific APIs**: Each robot has dedicated namespaces (`unitree::robot::g1`, `go2`, `h1`, etc.) with high-level clients (`LocoClient`, `SportClient`, `ArmActionClient`)
- **DDS Communication**: All robot communication uses publish/subscribe over DDS topics (e.g., `rt/lowstate`, `rt/lowcmd`)
- **IDL Messages**: Auto-generated message types in `include/unitree/idl/{robot}/` from IDL definitions
- **ChannelFactory Pattern**: Centralized DDS initialization via singleton `ChannelFactory::Instance()->Init(domain_id, network_interface)`

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
1. **WSL2 Configuration**: WSL2 can work with DDS but requires proper setup:
   - **Check network mode**: WSL2 mirrored networking (Windows 11 22H2+) works best
   - **Verify interface**: Use interface that matches your Windows adapter (use `ip a`)
   - **CycloneDDS config**: May need to specify interface explicitly in cyclonedds.xml
   - **Try different interfaces**: Test with all available interfaces (eth0, eth1, wlan0)
2. Check `CYCLONEDDS_URI` points to valid [cyclonedds.xml](cyclonedds.xml)
3. Verify network interface name (use `ip a` to find `eth0`, `wlan0`, `eth1`, etc.)
4. Firewall must allow UDP ports 7400-7430 (DDS discovery)
5. **G1 Air limitation**: Without NX access, you depend on robot's pre-configured network settings
6. Check if robot SDK mode is enabled in Unitree app settings

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

# Run robot example (replace eth0 with your interface)
./build/bin/g1_loco_client --network_interface=eth1 --get_fsm_mode

# Capture Android app traffic to reverse-engineer protocol
./capture_robot_traffic.sh  # Run while using Android app
```

## Replicating Android App Functionality (G1 Air)

Since the G1 Air lacks secondary development mode, you're working in the same client-server model as the Android app:

### 1. Network Discovery & Traffic Analysis
Note: The Android app binds to a specific robot (e.g., G1_6937). Once bound and connected (green indicator), the robot is reachable on the network.

```bash
# Identify what the Android app is doing (replace IP with your robot's IP)
sudo tcpdump -i eth1 host 192.168.86.3 -w android_traffic.pcap
# Use Android app while capturing, then analyze:
wireshark android_traffic.pcap  # Look for DDS topics, ports, message patterns
```

### 2. Control Path
The Android app likely uses:
- **High-level APIs**: `g1::LocoClient` for movement, `g1::G1ArmActionClient` for arm gestures
- **DDS topics**: Direct subscription to `rt/lowstate` for real-time sensor data
- **Service calls**: Mode switching via `MotionSwitcherClient`

Start with [example/g1/high_level/g1_loco_client_example.cpp](example/g1/high_level/g1_loco_client_example.cpp) - this shows command-line control similar to app buttons.

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
