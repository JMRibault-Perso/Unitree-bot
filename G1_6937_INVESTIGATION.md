# G1_6937 SDK Investigation Summary

## Robot Information
- **Model**: G1 Air
- **Serial**: G1_6937
- **IP Address**: 192.168.86.3
- **Network**: WiFi (STA mode on 192.168.86.x)

## Control Methods Tested

### ✓ Working
1. **Android App** - Full control, status, video streaming
2. **R3-1 Remote Control** - Direct radio control

### ✗ Not Working
3. **SDK/DDS** - No DDS broadcast detected

## Testing Results (Native Ubuntu)

### Network Connectivity
- ✓ Robot pingable (192.168.86.3)
- ✓ Network interface configured (eth1: 192.168.86.12/22)
- ✓ Multicast groups enabled
- ✓ No firewall blocking

### DDS Communication
- ✗ Zero packets on DDS ports (7400-7430)
- ✗ Zero packets of any kind from robot
- ✗ test_subscriber receives nothing
- ✗ Unicast/multicast both failed

### Configuration Attempts
- ✓ CYCLONEDDS_URI set correctly
- ✓ Correct network interface (eth1)
- ✓ Tried on WSL2 and native Ubuntu
- ✓ Tried explicit interface configuration
- ✓ Tried peer-based discovery

## Conclusion

**The G1 Air (G1_6937) does not broadcast continuous DDS topics (subscription/publish mode).**

Evidence:
1. No developer/SDK mode toggle in app
2. No developer/SDK mode on R3-1 remote
3. Zero DDS packets on native Ubuntu (ports 7400-7430)
4. Robot lacks Jetson Orin NX (EDU feature)

## Communication Architecture Discoveries (Jan 22, 2025)

### Official Unitree Documentation Findings

From [SDK Overview](https://support.unitree.com/home/en/G1_developer/sdk_overview):

**G1 supports TWO DDS communication modes:**

1. **Subscription/Publish Mode**
   - High/medium frequency continuous data
   - Receiver subscribes to topics, sender broadcasts to subscription list
   - Used for: `rt/lowstate`, `rt/lowcmd`, sensor streams
   - **Status on G1 Air (6937)**: ✗ NOT working (zero packets observed)

2. **Request/Response Mode** ⭐ NEW DISCOVERY
   - Question-and-answer mode (like REST API)
   - Low-frequency data acquisition or function switching
   - Request sent to topic, broadcast reply matched by UUID
   - **Two calling methods:**
     - API call: Direct topic request/response
     - Functional call: High-level API wrapper (what SDK examples use)
   - **Status on G1 Air**: ⚠️ UNTESTED - needs verification

### Architecture from [Architecture Description](https://support.unitree.com/home/en/G1_developer/architecture_description):

**Android App Communication Stack:**
- **Primary: WebRTC** for:
  - Audio/video streams
  - Radar point clouds
  - Motion status data
  - **Control instructions** (walking, arm movement)
- Secondary: MQTT for cloud services (OTA updates, signaling)
- Bluetooth: Network configuration and security verification

**G1 EDU vs G1 Air:**
- **EDU**: Has PC2 at `192.168.123.164` for secondary development with DDS/ROS2
- **Air**: No secondary development PC (confirmed limitation)

### Implications for G1_6937 Control

**Why we see zero DDS traffic:**
- G1 Air does NOT broadcast continuous state topics (`rt/lowstate`)
- Subscription/publish mode likely disabled on non-EDU models

**What might still work:**
1. **Request/Response API calls** (high-level clients):
   - `g1::LocoClient::GetFsmMode()` - sends request, waits for reply
   - `g1::ArmActionClient` - triggers pre-programmed actions
   - These use DDS request/response, not continuous streams
   - May work even without state broadcasts
   
2. **WebRTC control** (what Android app actually uses):
   - Direct video/audio streaming
   - Control commands sent over WebRTC data channel
   - Requires reverse-engineering app's WebRTC/MQTT signaling

## Next Steps (Updated Priority)

### Priority 1: Test Request/Response DDS API
The SDK's high-level clients use request/response mode, NOT subscription/publish:
```bash
# Test if request/response DDS works (even without state broadcasts)
export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml
export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH
./build/bin/g1_loco_client --network_interface=eth1 --get_fsm_mode
```

**If this works**, you can use all high-level SDK APIs:
- `LocoClient` for movement control
- `ArmActionClient` for arm gestures
- `AudioClient` for TTS/ASR
- `MotionSwitcherClient` for mode switching

### Priority 2: Reverse-Engineer WebRTC Protocol
The Android app uses WebRTC for all real-time control and video:
```bash
# Capture Android app's WebRTC/MQTT signaling
sudo tcpdump -i eth1 host 192.168.86.3 -w webrtc_capture.pcap
# Use Android app while capturing
wireshark webrtc_capture.pcap  # Look for:
# - MQTT topics (cloud signaling)
# - STUN/TURN negotiations
# - WebRTC data channel messages
# - Video codec (H.264/H.265)
```

**If you can replicate WebRTC handshake**, you get:
- Direct video streaming (same as app)
- Real-time control commands
- Bidirectional status updates

### Priority 3: Contact Unitree Support
- Email: support@unitree.com
- Serial: G1_6937 (G1 Air)
- **Specific questions**:
  1. "Does G1 Air support DDS request/response API (not subscription/publish)?"
  2. "What protocols does the Android app use (WebRTC/MQTT/DDS)?"
  3. "Can G1 Air be upgraded to enable SDK mode or continuous DDS broadcasts?"
  4. "Is there firmware to enable subscription/publish mode on G1 Air?"

### Option 1: Reverse-Engineer Android Protocol
Capture traffic while using the Android app to identify:
- Communication protocol (likely custom TCP/UDP)
- Message formats
- Control sequences

Command:
```bash
sudo tcpdump -i eth1 host 192.168.86.3 -w app_traffic.pcap
# Use Android app while capturing
wireshark app_traffic.pcap
```

### Option 2: Contact Unitree Support
- Email: support@unitree.com
- Serial: G1_6937
- Question: "Does G1 Air support SDK/DDS without Jetson Orin NX?"
- Request SDK-enabled firmware or upgrade path

### Option 3: Upgrade Hardware
- G1 EDU with Jetson Orin NX has full SDK support
- Includes SSH access, DDS topics, development environment
- Check for upgrade/trade-in options

## Files Created for Diagnosis
- `diagnose_dds.sh` - Comprehensive DDS diagnostics
- `wsl2_dds_check.sh` - WSL2-specific checks
- `capture_all_robot_traffic.sh` - Full traffic capture
- `.github/copilot-instructions.md` - Updated with G1 Air limitations

## References
- [Unitree G1 FAQ](https://support.unitree.com/home/en/G1_developer/FAQ)
- [DDS Communication Routine](https://support.unitree.com/home/en/G1_developer/dds_communication_routine)
- SDK documentation in `/root/G1/unitree_sdk2/`
