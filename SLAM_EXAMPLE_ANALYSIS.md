# SLAM Example Analysis - Key Findings

## Critical Discovery from Official Example

The Unitree SLAM example (`keyDemo.cpp`) reveals how SLAM service actually works:

### 1. Uses DDS Client API (not direct publish)
```cpp
class TestClient : public Client {
    // Inherits from unitree::robot::Client
    // Uses Call(api_id, parameter, data) method
};

// Example usage:
int32_t statusCode = Call(ROBOT_API_ID_START_MAPPING_PL, parameter, data);
```

**NOT** direct DDS publish like we're doing:
```python
conn.datachannel.pub_sub.publish("rt/api/slam_operate/request", payload)
```

### 2. Service Registration Pattern
```cpp
void TestClient::Init() {
    SetApiVersion("1.0.0.1");
    
    UT_ROBOT_CLIENT_REG_API_NO_PROI(ROBOT_API_ID_START_MAPPING_PL);
    UT_ROBOT_CLIENT_REG_API_NO_PROI(ROBOT_API_ID_END_MAPPING_PL);
    UT_ROBOT_CLIENT_REG_API_NO_PROI(ROBOT_API_ID_STOP_NODE);
    // etc...
}
```

The `UT_ROBOT_CLIENT_REG_API_NO_PROI` macro likely:
- Registers API endpoints with request/response topics
- Sets up proper message routing
- May use different topic naming than `rt/api/{service}/request`

### 3. Feedback Topics
```cpp
#define SlamInfoTopic "rt/slam_info"
#define SlamKeyInfoTopic "rt/slam_key_info"

// Subscribes to these topics for SLAM status
subSlamInfo->InitChannel(callback);
subSlamKeyInfo->InitChannel(callback);
```

### 4. WebRTC Wrapper Implication

Since:
- Android app works with SLAM (per user confirmation of LiDAR in app)
- Android app uses WebRTC (not direct DDS)
- Our web controller uses same WebRTC library
- SDK docs say "DDS is wrapped by WebRTC"

**Therefore**: The WebRTC datachannel must support the Client API pattern, but we're not using it correctly.

## Our Current Wrong Approach

```python
# What we're doing (WRONG):
await self.datachannel.pub_sub.publish(
    "rt/api/slam_operate/request",
    {"api_id": 1801, "parameter": "{...}"}
)
```

This assumes a simple request/response pattern like other APIs, but SLAM service likely requires the full Client API infrastructure.

## What We Need to Check

1. **Does unitree_webrtc_connect support Client API pattern?**
   - Check if there's a `Client` class or `call()` method
   - Look for service registration in the library
   
2. **Alternative: Direct topic publish might work**
   - The C++ Client.Call() might internally just publish to a topic
   - We need to find the ACTUAL topic name used
   - May not be `rt/api/{service}/request` format

3. **Network segment requirement**
   - Example requires network segment 123 (192.168.123.164 - Jetson NX)
   - G1 Air on WiFi network (192.168.86.18)
   - WebRTC might bridge this, or SLAM service might only run on NX network

## Next Steps

1. Examine `unitree_webrtc_connect` library for Client API support
2. Monitor ALL DDS traffic when Android app uses SLAM/LiDAR
3. Check if there's a different topic naming for SLAM service
4. Test if SLAM service is even available on G1 Air (might be EDU-only)

## Key Question

**Does G1 Air even support SLAM service?**

The documentation says:
> "The default IP address of the NX development board is 192.168.123.164"
> "ssh unitree@192.168.123.164"

NOT TRUE: -This implies SLAM service runs ON the Jetson NX board. G1 Air doesn't have NX, so SLAM service may not exist at all on this model.
THE ROBOT HAS LIDAR

**Hypothesis**: the android display the Lidar - can createa map and run path as well as patrols 
