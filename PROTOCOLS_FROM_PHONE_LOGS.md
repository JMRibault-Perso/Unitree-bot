# Unitree G1 Protocol Documentation (Extracted from Phone Logs)

## Summary
The Android app logs reveal the complete API protocol used to communicate with the robot via DDS topics over WebRTC data channel.

## Robot Discovery & Connection Protocol

### Robot Identity
- **Robot Name**: G1_6937
- **Robot MAC Address (WiFi)**: `fe:23:cd:92:60:02`
- **Default AP Password**: `88888888`

### Discovery Mechanism

**App Discovery Process:**
1. **BLE Scan**: App searches for BLE devices with MAC `fe:23:cd:92:60:02`
2. **BLE Handshake**: MTU negotiation → version exchange → MAC retrieval
3. **WiFi Credentials**: App sends SSID/password via BLE
4. **WiFi Connection**: Robot connects to specified network or stays in AP mode
5. **WebRTC Connection**: App establishes encrypted video/audio/data channel

### Network Modes

**1. AP Mode (Access Point)**
- Robot creates WiFi network `G1_6937`
- Robot IP: `192.168.12.1`
- App connects directly to robot's hotspot
- Status: `{"topic":"public_network_status","data":"{\"status\":\"AP\"}"}`

**2. STA-L Mode (Station - Local Network)**
- Robot and app on same WiFi network
- Example: Robot `192.168.86.3`, App `192.168.86.2`
- Status: `{"topic":"public_network_status","data":"{\"status\":\"STA-L\"}"}`

**3. STA-T Mode (Station - Offline/Remote)**
- Robot on WiFi but different network than app
- Requires cloud relay: `https://global-robot-api.unitree.com`
- Error when unreachable: `{"code":1000,"errorMsg":"device not online"}`

### BLE Pairing Protocol

```
Step 1: MTU Negotiation
  ble :设置mtu成功：23

Step 2: Version Exchange
  Send: [111, -19, 95, 59, 18, -127, -123, -85, -81, -119, -51, -43, -9]
  Recv: [hex=6ce65f3b1252]
  ble :解析版本号：1

Step 3: MAC Address Retrieval
  Send: [111, -28, 89, -103]
  Recv: [hex=6cea57c4303979a2d941]
  ble :mac：fe:23:cd:92:60:02

Step 4: WiFi Credentials (encrypted binary protocol)
  Send: [111, -27, 93, 59, -74]
  Send: [111, -19, 90, 59, 18, -77, -38, -99, -19, -62, -101, -121, -66]
  Send: [111, -18, 91, 59, 18, -52, -45, -6, -29, -61, -112, -120, 109, 0]
  Send: [111, -25, 88, 111, 64, -11, 19]
  
Step 5: Disconnection
  ble :设备已断开连接
```

### Network Change Detection

**WiFi Monitoring:**
```
WifiHelp :bssid: fe:23:cd:92:60:02  ---  wifi:<router_mac>
```
- First BSSID = Robot's WiFi interface (`fe:23:cd:92:60:02`)
- Second wifi = WiFi router MAC (e.g., `e0:d3:62:86:d8:f7`)
- If `wifi:null` → Robot disconnected from WiFi
- If `wifi:fe:23:cd:92:60:02` → Robot in AP mode

**Local Network Detection:**
```json
{"type":"0","data":"192.168.12.1","msg":""}  // Connection success
{"type":"1","data":"192.168.86.2","msg":""}  // Local network IP
{"type":"2","data":"https://global-robot-api.unitree.com","msg":""}  // Cloud API
{"type":"3","data":"192.168.12.1","msg":""}  // AP mode IP
```

### WebRTC Network Interfaces

**Robot exposes 3 IP addresses in ICE candidates:**

1. **169.254.x.x** - Link-local (direct device-to-device)
2. **192.168.x.x** - LAN IP (STA-L: router IP, AP: `192.168.12.1`)
3. **192.168.123.161** - Internal bridge (PC1 ↔ PC2, not accessible externally)

**Example ICE Candidates:**
```
a=candidate:2 1 udp 2130706431 169.254.62.11 52165 typ host
a=candidate:1 1 udp 2130706431 192.168.12.1 45168 typ host
a=candidate:0 1 udp 2130706431 192.168.123.161 54419 typ host
```

## Robot Hardware Information

**Serial Number**: `E21D1000PAHBMB06`  
**Model**: G1 Air  
**Series**: G1  
**Market**: 2 (Region code)

**JWT Token Structure** (for WebRTC authentication):
```json
{
  "alias": "G1_6937",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "sn": "E21D1000PAHBMB06",
  "series": "G1",
  "key": "",
  "model": "Air",
  "market": 2
}
```

**Decoded JWT Token**:
```json
{
  "sub": "user",
  "uid": 47442,
  "ct": 1768947999,
  "iss": "unitree_robot",
  "type": "access_token",
  "exp": 1771539999
}
```
- User ID: 47442
- Issued: 1768947999 (timestamp)
- Expires: 1771539999 (timestamp)
- Issuer: `unitree_robot`

## Security & Error Handling

### RSA Public Key (Cloud Communication)
Robot uses RSA encryption for cloud API communication:
```
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnOc1sgpzL4GTVp9/oQ0HD7eeAO2GJUABfjX3TitgXiXN1Ktn2WLsLrtAiIuj3OrrRogx8fCT16oxnXx/XrapBRHD/ufHZ08A2IRVw6U6vKDv8TpQH22sAEtUji4/P2AaZmeOxFsYW5FshQr37KBG+cBb7rJWLWEJpIXmCpnt37GGCtsACqRegkl7qQ8Q0OiJmtrYLPi00xSstZb+Wv1v8B0eTY3POAUXjgl357L5dc6vS99rYFkYeUCTWHaH4d51Z/KgCRYUadboDc2cgNg/z2dbO9S3HADegbIsN3fTbjDCruKfvc5ejxlFZ0Xbu6SScQbmkP8t3TPvy/DXGJAhNwIDAQAB
```

### Error Topic
Topic: `errors`  
Format: `{"topic":"errors","data":"[]","id":"0"}`

**Error Addition**:
```json
{"topic":"add_error","data":"[1769616901,200,1]","id":"0"}
```
- `[timestamp, error_code, priority]`
- Error code 200 observed in logs

**Error Removal**:
```json
{"topic":"rm_error","data":"[1769616905,200,1]","id":"0"}
```

### Error Codes Observed

| Code | Message | Meaning |
|------|---------|---------|
| 100 | SUCCESS | Command successful |
| 1000 | App cannot access the network | WiFi disconnected or wrong network |
| 1000 | device not online | Robot in STA-T mode (different network) |
| 1000 | Network exception | Cloud API unreachable |

### Multicast Timeout Pattern
```
connect :收到组播ip:timeout
```
- Robot attempts multicast discovery on local network
- Timeout indicates app/robot on different subnets or AP mode active

## Protocol Pattern

All commands use this format:
```json
{
  "api_id": <number>,
  "data": "<json_string>" or {},
  "id": <incremental_request_id>,
  "priority": false,
  "topic": "rt/api/<service>/request"
}
```

## Discovered Topics & APIs

### Topic Subscriptions

The app subscribes to real-time DDS topics via `appSendTopicSubscribe`:

**Subscription Pattern:**
```
开启订阅 = "Enable subscription" (Chinese for start)
关闭订阅 = "Disable subscription" (Chinese for stop)
```

**Discovered Subscribe/Unsubscribe Topics:**

**1. Arm Action State (`rt/arm/action/state`)**
```json
{"topic":"rt/arm/action/state","data":"{\"holding\": false, \"id\": -1, \"name\": \"2026-01-28_21:27:37\"}","id":"0"}
```
- Subscribed during teach mode (API 7110)
- Broadcasts at ~10Hz (100ms interval)
- Fields:
  - `holding`: boolean - whether currently recording
  - `id`: number - action ID (-1 = recording/custom action)
  - `name`: string - action name (timestamp or custom name)

**2. Log System (`rt/log_system_outbound`)**
- Subscribed when viewing system logs
- Broadcasts robot system log messages
- Used for debugging/diagnostics

**3. Network Status (`public_network_status`)**
```json
{"topic":"public_network_status","data":"{\"status\":\"STA-L\"}","id":"0"}
```
- Broadcast automatically on connection
- Status values:
  - `"AP"` - Robot in Access Point mode (creates WiFi network)
  - `"STA-L"` - Station mode, connected to local network
  - `"STA-T"` - Station mode, device not online

**4. Errors Topic (`errors`)**
```json
{"topic":"errors","data":"[]","id":"0"}
```
- Broadcast automatically on connection
- Array of error messages (empty = no errors)

**Expected Topics (Not Seen in Logs):**
Based on SDK documentation, these topics should exist but weren't captured:
- `rt/slam_info` - SLAM real-time state (battery, pose, map info)
- `rt/slam_key_info` - SLAM task results (navigation completion)
- `rt/unitree/slam_mapping/points` - Point cloud during mapping (PointCloud2)
- `rt/unitree/slam_mapping/odom` - Odometry during mapping
- `rt/unitree/slam_relocation/points` - Point cloud during navigation
- `rt/unitree/slam_relocation/odom` - Odometry during navigation
- `rt/unitree/slam_relocation/global_map` - Full loaded map
- `rt/lf/sportmodestate` - FSM state for movement control
- `rt/lf/bms` - Battery Management System state
- `rt/utlidar/cloud_livox_mid360` - LiDAR point cloud data
- `rt/audio_msg` - Speech recognition results (ASR)

### 1. Arm Control (`rt/api/arm/request`)

**API 7107 - Get Action List:**
```json
{"api_id":7107,"data":"","id":1,"priority":false,"topic":"rt/api/arm/request"}
```

**API 7110 - Record Custom Action (Teach Mode):**
```json
{"api_id":7110,"data":"{\"action_name\":\"2026-01-28_21:27:37\"}","id":4,"priority":false,"topic":"rt/api/arm/request"}
```
- Starts recording arm positions
- action_name format: `YYYY-MM-DD_HH:MM:SS` (auto-generated timestamp)
- Keep-alive during recording: Send with empty action_name every ~1 second
- Stop recording: `{"api_id":7110,"data":"","id":17,"priority":false,"topic":"rt/api/arm/request"}`

**API 7108 - Execute Custom Action:**
```json
{"api_id":7108,"data":"{\"action_name\":\"2026-01-28_21:27:37\"}","id":19,"priority":false,"topic":"rt/api/arm/request"}
```
- Plays back a recorded gesture
- action_name can be timestamp or renamed custom name

**API 7109 - Rename Action:**
```json
{"api_id":7109,"data":"{\"pre_name\":\"2026-02-06_08:46:34\",\"new_name\":\"touch me not\"}","id":17,"priority":false,"topic":"rt/api/arm/request"}
```
- Renames a taught action from timestamp to custom name
- `pre_name`: Current action name (usually auto-generated timestamp)
- `new_name`: New custom name for the action

**API 7113 - Stop Action:**
```json
{"api_id":7113,"data":"","id":20,"priority":false,"topic":"rt/api/arm/request"}
```
- Emergency stop for currently executing action

### 2. Motion Switcher (`rt/api/motion_switcher/request`)

**API 1001 - Get Current Mode:**
```json
{"api_id":1001,"data":"","id":1,"priority":false,"topic":"rt/api/motion_switcher/request"}
```

### 3. System Services (`rt/api/bashrunner/request`)

**API 1001 - Run Bash Script:**
```json
{"api_id":1001,"data":"{\"script\":\"get_software_version.sh\"}","id":1,"priority":false,"topic":"rt/api/bashrunner/request"}
```

## SLAM/Navigation

**Accessing SLAM UI:**
The app navigates to a web interface at `/newSlam` with parameters:
```json
{
  "url": "/newSlam",
  "from": "",
  "language": "en",
  "mode": "air",
  "userid": "47442",
  "debugger": "0",
  "sn": "E21D1000PAHBMB06",
  "sportmode": "ai",
  "series": "G1",
  "pid": "0",
  "topLeft": 42.166668
}
```

**CRITICAL**: `/newSlam` is accessed via **WebRTC data channel**, NOT traditional HTTP/HTTPS:
- The robot runs an internal web server
- The `/newSlam` endpoint is loaded through the encrypted WebRTC tunnel
- This is why SLAM operations (map creation, patrol waypoints) don't appear in `appSendCmdToGo2` logs
- The web interface communicates with the robot via HTTP/WebSocket internally, bypassing DDS command logging
- **Not accessible from external browsers** - requires active WebRTC connection

**SLAM Service (from SDK documentation):**
- Service name: `slam_operate` (version 1.0.0.1)
- Topic: `rt/api/slam_operate/request`
- Status: 0 (running)

**SLAM APIs (Official SDK):**

**API 1801 - Start Mapping:**
```json
{"api_id":1801,"data":"{\"slam_type\":\"indoor\"}","id":1,"priority":false,"topic":"rt/api/slam_operate/request"}
```

**API 1802 - End Mapping (Save Map):**
```json
{"api_id":1802,"data":"{\"address\":\"/home/unitree/Basement.pcd\"}","id":2,"priority":false,"topic":"rt/api/slam_operate/request"}
```
- **"address"** field contains the full path where map will be saved
- Example: `/home/unitree/Basement.pcd`

**API 1804 - Initialize Pose (Load Map):**
```json
{"api_id":1804,"data":"{\"x\":0.0,\"y\":0.0,\"z\":0.0,\"q_x\":0.0,\"q_y\":0.0,\"q_z\":0.0,\"q_w\":1.0,\"address\":\"/home/unitree/Basement.pcd\"}","id":3,"priority":false,"topic":"rt/api/slam_operate/request"}
```
- **"address"** field contains the full path of map to load
- Initial pose sets robot's starting position in the loaded map

**API 1102 - Pose Navigation:**
```json
{"api_id":1102,"data":"{\"targetPose\":{\"x\":2.0,\"y\":0.0,\"z\":0.0,\"q_x\":0.0,\"q_y\":0.0,\"q_z\":0.0,\"q_w\":1.0},\"mode\":1}","id":4,"priority":false,"topic":"rt/api/slam_operate/request"}
```
- Navigate to target pose within loaded map
- Max distance: 10 meters from current position

**API 1201 - Pause Navigation:**
```json
{"api_id":1201,"data":"{}","id":5,"priority":false,"topic":"rt/api/slam_operate/request"}
```

**API 1202 - Resume Navigation:**
```json
{"api_id":1202,"data":"{}","id":6,"priority":false,"topic":"rt/api/slam_operate/request"}
```

**API 1901 - Close SLAM:**
```json
{"api_id":1901,"data":"{}","id":7,"priority":false,"topic":"rt/api/slam_operate/request"}
```

## Service State Topic

**Topic: `rt/servicestate`**
Returns all running services with version info, status, and protection level:
```json
{
  "topic": "rt/servicestate",
  "data": "[{\"name\":\"ai_sport\",\"protect\":0,\"status\":0,\"version\":\"8.5.1.1\"}]"
}
```

**Complete Service List (G1 Air):**
| Service | Version | Status | Protect | Description |
|---------|---------|--------|---------|-------------|
| `ai_sport` | 8.5.1.1 | 0 (running) | 0 | AI-powered motion control |
| `audio_player_service` | - | 0 | 0 | Audio playback |
| `auto_test_arm` | - | 1 (stopped) | 0 | Arm testing utility |
| `auto_test_low` | - | 1 (stopped) | 0 | Low-level testing utility |
| `bashrunner` | 1.0.3.1 | 0 | 0 | Shell script executor |
| `basic_service` | 1.0.1.37 | 0 | 1 | **Core system service (protected)** |
| `battery_guard` | 1.0.0.2 | 0 | 0 | Battery monitoring/protection |
| `chat_go` | 1.9.2.13 | 0 | 0 | Voice interaction (ASR/TTS) |
| `dex3_service_l` | - | 0 | 0 | Left hand dexterity service |
| `dex3_service_r` | - | 0 | 0 | Right hand dexterity service |
| `g1_arm_example` | 2.0.0.19 | 0 | 0 | Arm gesture control |
| `lidar_driver` | 1.0.0.5 | 0 | 0 | LiDAR sensor driver |
| `log_system` | 1.0.0.10 | 0 | 0 | System logging service |
| `master_service` | 1.2.1.2 | 0 | 1 | **Master coordinator (protected)** |
| `motion_switcher` | 1.0.0.1 | 0 | 0 | Motion mode switcher |
| `net_switcher` | 1.0.2.1 | 0 | 0 | Network mode switcher (AP/STA) |
| `ota_box` | - | 1 (stopped) | 0 | Over-the-air updates |
| `robot_state` | 1.2.3.6 | 0 | 1 | **Robot state manager (protected)** |
| `robot_type_service` | 1.0.1.3 | 0 | 0 | Robot model identification |
| `ros_bridge` | 1.0.0.4 | 0 | 0 | ROS integration bridge |
| `state_estimator` | 1.0.0.3 | 0 | 0 | IMU/odometry state estimation |
| `unitree_slam` | 1.0.2.1 | 0 | 0 | SLAM mapping/navigation |
| `video_hub` | 1.0.1.1 | 0 | 0 | Video stream manager |
| `vui_service` | 2.1.0.12 | 0 | 0 | Voice UI / TTS / Audio |
| `webrtc_bridge` | 1.0.8.10 | 0 | 1 | **WebRTC communication (protected)** |
| `webrtc_multicast_responder` | - | 0 | 0 | WebRTC multicast handler |
| `webrtc_signal_server` | - | 0 | 1 | **WebRTC signaling (protected)** |

**Key Notes:**
- `protect: 1` = Critical system service, cannot be stopped
- `status: 0` = Running, `status: 1` = Stopped
- Protected services: basic_service, master_service, robot_state, webrtc_bridge, webrtc_signal_server

## WebRTC Connection

The app uses WebRTC for video/audio streaming and data channel for command/control:

**Media Streams:**
- **Video**: H.264 encoded, 90kHz clock rate (90000 Hz RTP clock)
  - Codec: H264/90000
  - Profile: level-asymmetry-allowed=1, packetization-mode=1, profile-level-id=42e01f
  - Features: NACK (negative acknowledgment), goog-remb (bandwidth estimation), transport-cc (congestion control)
- **Audio**: Opus encoded, 48kHz stereo, 2 channels
  - Codec: opus/48000/2
  - Features: minptime=10ms, useinbandfec=1 (forward error correction)
  - Same feedback features as video: NACK, goog-remb, transport-cc
- **Data Channel**: SCTP over DTLS for DDS message tunneling
  - Port: 5000 (SCTP port)
  - Protocol: UDP/DTLS/SCTP webrtc-datachannel
  - Purpose: Tunnels all DDS API commands and responses

**WebRTC SDP Structure:**
```
v=0 (SDP version)
o=- <session_id> 2 IN IP4 127.0.0.1
s=- (session name, empty)
t=0 0 (timing: permanent session)
a=group:BUNDLE 0 1 2 (bundle all 3 media types)
a=msid-semantic: WMS myKvsVideoStream (media stream ID semantic)

m=video 9 UDP/TLS/RTP/SAVPF 119 (video on port 9, payload type 119)
  a=candidate: (ICE candidates - robot's local network addresses)
    - candidate:2 = 169.254.62.11 (link-local)
    - candidate:1 = 192.168.12.1 or 192.168.86.3 (LAN IP)
    - candidate:0 = 192.168.123.161 (robot internal network)
  a=ice-ufrag:xxxx (ICE username fragment)
  a=ice-pwd:xxxxxxxxxxxx (ICE password)
  a=fingerprint:sha-256 <hash> (DTLS certificate fingerprint)
  a=setup:active (robot initiates DTLS handshake)
  a=mid:0 (media ID 0 = video)
  a=sendonly (robot only sends video, app receives)
  a=rtcp-mux (RTP and RTCP multiplexed on same port)

m=audio 9 UDP/TLS/RTP/SAVPF 111 (audio on port 9, payload type 111)
  (same ICE/DTLS config as video)
  a=mid:1 (media ID 1 = audio)
  a=sendrecv (bidirectional audio - robot can send/receive)

m=application 9 UDP/DTLS/SCTP webrtc-datachannel (data channel)
  (same ICE/DTLS config)
  a=mid:2 (media ID 2 = data channel)
  a=sctp-port:5000 (SCTP port number)
```

**Connection Discovery (ICE):**
- WebRTC uses STUN/TURN for NAT traversal (no external servers needed for local network)
- Robot advertises 3 network interfaces:
  1. Link-local (169.254.x.x) - auto-configured fallback
  2. LAN IP (192.168.x.x) - main network interface
  3. Internal network (192.168.123.161) - robot's internal PC communication
- App selects best candidate based on network topology
- Connection established via UDP hole-punching

**Security:**
- DTLS encryption for all media and data
- SHA-256 fingerprint verification
- Unique ICE credentials per session (ice-ufrag, ice-pwd)
- TLS-like handshake for key exchange

**Data Channel Protocol:**
All DDS commands/responses flow through the SCTP data channel:
- App sends: `appSendCmdToGo2` → WebRTC data channel → Robot DDS topic
- Robot responds: DDS response → WebRTC data channel → `webSendCmdRes` in app
- Topic subscriptions: `appSendTopicSubscribe` enables/disables real-time DDS message streaming

## SLAM Map Storage

Based on SDK documentation and code analysis:
- **Location**: Specified in "address" field of API calls
- **Default pattern**: `/home/unitree/{map_name}.pcd`
- **Format**: Point Cloud Data (.pcd)
- **Recommended names**: `test1.pcd` through `test10.pcd` (SDK recommendation to save disk space)
- **Custom names**: User-defined (e.g., "Basement.pcd")

**CRITICAL**: The map name is **always specified in the "address" field** when saving (API 1802) or loading (API 1804).
- Example save: `"address": "/home/unitree/Basement.pcd"`
- Example load: `"address": "/home/unitree/Basement.pcd"`

**To find your "Basement" map:**
Your map should be at `/home/unitree/Basement.pcd` (exact case as you typed in the app)

## SLAM Status Topics (from SDK)

**rt/slam_info** - Real-time broadcast information:
- `type: "robot_data"` - Battery, motor temps, CPU usage
- `type: "pos_info"` - Current pose and loaded map info (includes "pcdName" and "address")
- `type: "ctrl_info"` - Navigation control state

**rt/slam_key_info** - Task execution feedback:
- `type: "task_result"` - Navigation completion status

**rt/unitree/slam_mapping/points** - Real-time mapping point cloud (PointCloud2)
**rt/unitree/slam_mapping/odom** - Real-time mapping odometry (Odometry)
**rt/unitree/slam_relocation/points** - Relocation point cloud (PointCloud2)
**rt/unitree/slam_relocation/odom** - Relocation odometry (Odometry)
**rt/unitree/slam_relocation/global_map** - Full loaded map (sent once after relocation starts)

## Missing Data (Not Found in Logs)

**No SLAM operations in current logs** - The logs don't contain any mapping, loading, or navigation commands. This means:
- You haven't created or loaded any maps during the log period (Jan 27 - Feb 5)
- The SLAM UI was opened but no map operations were performed
- To capture SLAM APIs, you would need to:
  1. Start a new mapping session in the app
  2. Save the map with a name
  3. Load an existing map
  4. Navigate to a waypoint
  
Then the logs would show the actual API calls with your map names in the "address" field.

## Action Items

1. **Find SLAM map list API**: Capture logs while using SLAM navigation feature in app
2. **Test map naming**: Try loading "Basement.pcd" via your existing load_map API
3. **Reverse engineer APK**: Search decompiled code for "slam" + "map" + "list" keywords
4. **Check app database**: The map list might be cached locally in the app's SQLite database

## Files to Analyze Further

You've already pulled:
- `unitree_app.apk` (202 MB) - Decompile and search for SLAM APIs
- `unitree_full_pull/cache/log/*` - App logs with protocol messages
- `phone_logs_commands.txt` - Extracted command history

Next step: Decompile the APK and search for:
- Class names: `SlamMap`, `MapManager`, `NavigationController`
- API constants: `7150-7200` range (likely SLAM API IDs)
- String resources: "map_list", "get_maps", "saved_maps"
