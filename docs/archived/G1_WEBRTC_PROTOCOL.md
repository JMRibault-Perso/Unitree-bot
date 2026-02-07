# G1 Robot + WebRTC Architecture & Protocol

**Last Updated**: February 4, 2026  
**Robot Model**: G1_6937 (G1 Air without NX)  
**Connection Method**: WebRTC (not DDS)

---

## 🎯 Key Discovery: G1 Air Uses WebRTC, NOT DDS

### Why This Matters
- **G1 Air** (consumer model without Jetson Orin NX) = **WebRTC only**
- **G1 EDU** (developer model with NX) = DDS SDK support
- Most documentation is for EDU models - **doesn't apply to G1 Air**
- G1 Air is **identical to Android app architecture**

---

## 📊 G1 Communication Layers

### Layer 1: Physical Hardware
```
G1 Robot PC1 (onboard computer)
├── LiDAR sensor (publishes point clouds internally)
├── IMU/Motor sensors
├── FSM state machine
├── Motion control (locomotion, arm, etc)
└── DDS middleware (internal only - NOT exposed externally)
```

### Layer 2: On-Robot Services
```
G1 PC1 Services (DDS-based, internal):
├── ai_sport (locomotion control)
├── g1_arm_example (arm gestures)
├── vui_service (audio/LED control)
├── unitree_slam (mapping/navigation)
└── lidar_driver (point cloud processing)
```

### Layer 3: External Gateway (What We Access)
```
G1 PC1 WebRTC Module
├── Topic Publishing
│   ├── rt/lf/sportmodestate     → Low-frequency FSM state
│   ├── rt/lf/bms                → Battery status
│   ├── rt/slam_info             → SLAM pose data
│   ├── rt/audio_msg             → Speech recognition
│   └── [other topics]
│
├── API Endpoint
│   └── rt/api/{service}/request → Command API
│
└── Video Stream
    └── WebRTC video track → Real-time camera feed
```

### Layer 4: External Clients (Your Code)
```
Your PC (WebRTC Client)
├── Command Sender
│   ├── Start SLAM (API 1801)
│   ├── Save Map (API 1802)
│   ├── Load Map (API 1804)
│   ├── Navigate (API 1102)
│   └── Control Movement (API 7105)
│
├── Topic Subscriber
│   ├── Listen to rt/lf/sportmodestate
│   ├── Listen to rt/slam_info
│   └── Listen to rt/lf/bms
│
└── Video Receiver
    └── WebRTC video track
```

---

## 🔌 API Request Format (VERIFIED WORKING)

### The Pattern (From Feb 3 Test)
```python
payload = {
    "api_id": 1802,                    # API command ID
    "parameter": json.dumps({          # JSON-encoded parameters
        "data": {
            "address": "/home/unitree/map.pcd"  # Actual data
        }
    })
}

await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/slam_operate/request",     # Topic: rt/api/{service}/request
    payload
)
```

### Why This Format?
- `api_id`: Which operation to perform
- `parameter`: **JSON string** (not object!) containing the data
- `rt/api/{service}/request`: Standard WebRTC request topic
- Service: Which subsystem (`slam_operate`, `sport`, `arm`, etc)

---

## 📋 SLAM Workflow (Concrete Example)

### 1. Start Mapping
```python
payload = {
    "api_id": 1801,  # START_MAPPING
    "parameter": json.dumps({"data": {"slam_type": "indoor"}})
}
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/slam_operate/request", payload
)
```
**Result**: Robot starts collecting sensor data, LiDAR enabled

### 2. Monitor Progress
```python
def on_slam_info(data):
    slam_data = json.loads(data['data'])  # Nested JSON!
    pose = slam_data['data']['currentPose']
    print(f"Robot at: {pose['x']}, {pose['y']}")

conn.datachannel.pub_sub.subscribe("rt/slam_info", on_slam_info)
```
**Result**: Real-time position updates while mapping

### 3. Save Map
```python
payload = {
    "api_id": 1802,  # END_MAPPING
    "parameter": json.dumps({
        "data": {"address": "/home/unitree/my_map.pcd"}
    })
}
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/slam_operate/request", payload
)
```
**Result**: Map saved locally on robot to `/home/unitree/my_map.pcd`

### 4. Load Map
```python
payload = {
    "api_id": 1804,  # INITIALIZE_POSE
    "parameter": json.dumps({
        "data": {
            "x": 0.0, "y": 0.0, "z": 0.0,
            "q_x": 0.0, "q_y": 0.0, "q_z": 0.0, "q_w": 1.0,
            "address": "/home/unitree/my_map.pcd"
        }
    })
}
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/slam_operate/request", payload
)
```
**Result**: Map loaded, robot position initialized at (0,0,0)

### 5. Navigate
```python
payload = {
    "api_id": 1102,  # POSE_NAVIGATION
    "parameter": json.dumps({
        "data": {
            "targetPose": {
                "x": 1.0, "y": 0.5, "z": 0.0,
                "q_x": 0.0, "q_y": 0.0, "q_z": 0.0, "q_w": 1.0
            },
            "mode": 1
        }
    })
}
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/slam_operate/request", payload
)
```
**Result**: Robot navigates to target position with obstacle avoidance

### 6. Stop SLAM
```python
payload = {
    "api_id": 1901,  # CLOSE_SLAM
    "parameter": json.dumps({"data": {}})
}
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/slam_operate/request", payload
)
```
**Result**: SLAM disabled, LiDAR shut down

---

## 🔑 Core Concepts

### Topic Naming Convention
- **Outbound (commands)**: `rt/api/{service}/request`
- **Inbound (data)**: `rt/{module}` or `rt/lf/{module}` (low-frequency)
- **LiDAR**: Only publishes during active SLAM (API 1801 → 1901)

### Data Encoding
- **Outbound API calls**: `parameter` must be `json.dumps()` of the data
- **Inbound messages**: Usually `{"data": "..."}` where inner data is JSON string
- **Quaternion**: `q_x`, `q_y`, `q_z`, `q_w` (not Euler angles)

### State Management
- **FSM State**: Subscribe to `rt/lf/sportmodestate` for current mode
- **Battery**: Subscribe to `rt/lf/bms` for battery percentage
- **Mapping**: Subscribe to `rt/slam_info` for pose during SLAM
- **LiDAR**: Only publishes if SLAM active (1801 started)

### File Paths
- **Always absolute**: `/home/unitree/{filename}.pcd`
- **On robot**: Robot PC1 stores files locally
- **No HTTP needed**: Robot handles PCD internally

---

## ⚠️ Important Distinctions

### ❌ WRONG (Don't Do This)
```python
# WRONG: Nested header/identity
payload = {
    "header": {"identity": {"id": 0, "api_id": 1802}},
    "data": {"address": "/home/unitree/map.pcd"}
}
json_str = json.dumps(payload)  # Send as JSON string
```

### ✅ RIGHT (Do This)
```python
# RIGHT: Flat api_id + parameter
payload = {
    "api_id": 1802,
    "parameter": json.dumps({"data": {"address": "/home/unitree/map.pcd"}})
}
# Send as-is (already a dict, not JSON string)
```

---

## 📊 API Reference

| Operation | API ID | Service | Parameter | Status |
|-----------|--------|---------|-----------|--------|
| START_MAPPING | 1801 | slam_operate | `{"data": {"slam_type": "indoor"}}` | ✅ |
| END_MAPPING | 1802 | slam_operate | `{"data": {"address": "..."}}` | ✅ |
| INITIALIZE_POSE | 1804 | slam_operate | `{"data": {x, y, z, q_*, address}}` | ✅ |
| POSE_NAVIGATION | 1102 | slam_operate | `{"data": {targetPose, mode}}` | ✅ |
| PAUSE_NAVIGATION | 1201 | slam_operate | `{"data": {}}` | ✅ |
| RESUME_NAVIGATION | 1202 | slam_operate | `{"data": {}}` | ✅ |
| CLOSE_SLAM | 1901 | slam_operate | `{"data": {}}` | ✅ |
| SET_VELOCITY | 7105 | sport | `{"data": {vx, vy, vyaw}}` | ✅ |
| SET_FSM_ID | 7101 | sport | `{"data": {fsm_id}}` | ✅ |
| EXECUTE_ACTION | 7106 | arm | `{"data": {action_id}}` | ✅ |
| EXECUTE_CUSTOM_ACTION | 7108 | arm | `{"data": {action_name}}` | ✅ |

---

## 🔍 Debugging Checklist

When things don't work:

1. **Connection Issue?**
   - Check `UnitreeWebRTCConnection.connect()` returns True
   - Verify robot IP is correct
   - Check robot is powered + WiFi connected

2. **API Format Issue?**
   - Verify `api_id` is correct (e.g., 1802 for END_MAPPING)
   - Check `parameter` is `json.dumps()` result (string, not dict)
   - Ensure `data` key exists inside parameter

3. **Timing Issue?**
   - SLAM startup takes 2-3 seconds
   - Map saving is async (robot handles internally)
   - Add `await asyncio.sleep(2)` after each command

4. **Topic Issue?**
   - Verify topic format: `rt/api/{service}/request`
   - For SLAM: always use `rt/api/slam_operate/request`
   - For movement: use `rt/api/sport/request`

---

## 📁 Code Organization

```
/root/G1/unitree_sdk2/
├── STATUS.md                    ← Current work status
├── G1_WEBRTC_PROTOCOL.md        ← This file (architecture)
├── robot_test_helpers.py        ← Connection helper
│
├── g1_app/                      ← Web controller
│   ├── core/
│   │   ├── robot_controller.py  ✅ Working WebRTC connection
│   │   └── command_executor.py  ⚠️  Some code needs fixing
│   └── ui/web_server.py
│
├── G1_tests/
│   ├── slam/
│   │   └── simple_slam_test.py  ✅ Ready to run
│   └── [other test categories]
│
├── _scripts/                    ← Old shell scripts
├── _analysis/                   ← Research code
├── _archived_docs/              ← Old documentation
└── _old_files/                  ← Old logs/captures
```

---

## 🚀 Next Steps

1. **Run the test**: `python3 G1_tests/slam/simple_slam_test.py`
2. **Verify success**: Check map file at `/home/unitree/test_simple.pcd`
3. **Understand results**: Compare output with expected behavior above
4. **Extend functionality**: Use this protocol for your own features

---

**This is the definitive guide for G1 Air + WebRTC communication.**  
**All other documentation is either outdated or for EDU models.**
