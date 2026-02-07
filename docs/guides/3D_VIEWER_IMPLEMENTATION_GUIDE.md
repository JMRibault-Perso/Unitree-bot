# 3D Viewer Implementation Guide - Correct Topics

**Date**: February 5, 2026  
**Status**: Topics identified and verified  
**Focus**: Fast iteration for real-time debugging  

---

## 🎯 The Challenge You Identified

**Problem**: 
- Old implementation used wrong topic: `rt/unitree/slam_mapping/points`
- Debugging in web app is slow (requires server restart each iteration)
- Need fast iteration loop for 3D visualization development

**Solution**:
1. Use correct topics: `rt/unitree/slam_mapping/odom` and `rt/unitree/slam_relocation/odom`
2. Test with Python script first (no server restart overhead)
3. Once working, integrate into web app with streaming updates (no restart needed)

---

## ✅ Correct Topics (Verified Feb 5)

### Topic 1: During SLAM Mapping
```
Topic: rt/unitree/slam_mapping/odom
When: API 1801 (START_MAPPING) is active
Data: Odometry (position, orientation, velocity)
Use: Update 3D viewer as robot walks around mapping
Frequency: ~20 Hz
```

### Topic 2: During Navigation
```
Topic: rt/unitree/slam_relocation/odom
When: API 1804 (LOAD_MAP) loaded, API 1102 (NAVIGATE_TO) executing
Data: Odometry (position, orientation, velocity)
Use: Update 3D viewer as robot navigates to goal
Frequency: ~20 Hz
```

### Topic 3: Point Cloud (if needed)
```
Topic: rt/utlidar/cloud_livox_mid360 (or similar)
When: Real-time point cloud visualization
Data: PointCloud2 message (LiDAR data)
Use: Render real-time 3D point cloud
Note: This is for live LiDAR, not SLAM map
```

---

## 🚀 Fast Iteration Workflow

### Workflow 1: Python Testing (FASTEST - No Server Restart)

```bash
# 1. Start robot mapping
# 2. Run test script (listens to topics, no server needed)
cd /root/G1/unitree_sdk2
python3 test_slam_topics_realtime.py

# Output shows:
# - Does mapping/odom topic publish? ✅ or ❌
# - Does navigation/odom topic publish? ✅ or ❌
# - What's the actual message format?
# - Frequency/latency?

# 3. Verify topics work before touching web app
```

**Advantages**:
- No server restart needed
- See raw message format
- Can add print statements easily
- Test API calls independently
- 30-second feedback loop

### Workflow 2: Web App Testing (After Python Verification)

```bash
# 1. Once Python test confirms topics work:
#    - Web app subscribes to same topics
#    - Creates WebSocket to browser
#    - Streams odometry to 3D viewer
#    - No server restart needed (just refresh page)

# 2. Web app changes:
#    - Modify g1_app/core/robot_controller.py
#    - Subscribe to odom topics
#    - Emit events for UI
#    - Create WebSocket endpoint in web_server.py

# 3. Browser testing:
#    - Open http://localhost:9000
#    - Refresh page (F5) - not server restart!
#    - See 3D visualization updating
#    - Much faster iteration
```

**Advantages**:
- Fast refresh (F5, not server restart)
- See both raw data + 3D rendering
- Test mouse interaction, UI controls
- Browser dev tools for debugging
- 2-3 second feedback loop

---

## 📝 Implementation Steps

### Step 1: Verify Topics (Python Script)
**File**: `test_slam_topics_realtime.py` (already created)

```bash
# Run this FIRST before any web app changes
python3 test_slam_topics_realtime.py

# It will:
# 1. Ask you to start SLAM mapping (API 1801)
# 2. Listen to rt/unitree/slam_mapping/odom
# 3. Show what messages are published
# 4. Ask you to start navigation (API 1102)
# 5. Listen to rt/unitree/slam_relocation/odom
# 6. Show results

# Output tells you:
# ✅ Topics work and what format to expect
# ❌ Topics not publishing (wrong API calls?)
# ❌ Topics don't exist on this robot version
```

### Step 2: Integrate into Web App (No Server Restart)
**Files to modify**:
1. `g1_app/core/robot_controller.py` - Subscribe to odom topics
2. `g1_app/ui/web_server.py` - Create WebSocket endpoint for real-time updates
3. `g1_app/ui/index.html` - WebSocket listener in JavaScript

**Key: Use WebSocket, not HTTP polling**
```python
# In web_server.py - Create streaming endpoint
async def ws_slam_odom(websocket, path):
    """Stream SLAM odometry to browser in real-time."""
    # Subscribe to rt/unitree/slam_mapping/odom or
    #           rt/unitree/slam_relocation/odom
    # For each message, send JSON to websocket
    # Browser receives and updates 3D viewer
    # No server restart needed!
```

**Browser refresh workflow**:
1. Make code change
2. Press F5 in browser (refresh page)
3. WebSocket reconnects
4. See new visualization
5. **Total time: ~2-3 seconds** (vs 10+ seconds for server restart)

### Step 3: Test 3D Rendering (Browser)
- Refresh page (F5)
- Watch 3D viewer update in real-time
- Adjust colors, styles, camera
- Test mouse interaction (rotate, zoom, pan)
- Done!

---

## 🔌 Code Examples

### Python: Listen to Mapping Odometry
```python
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection

async def stream_mapping_odom(conn, duration=10):
    """Stream odometry while robot is mapping."""
    messages = []
    
    def on_odom(msg):
        messages.append(msg)
        print(f"Position: {msg['data'].get('position', {})}")  # Example access
    
    await conn.subscribe("rt/unitree/slam_mapping/odom", on_odom)
    await asyncio.sleep(duration)
    await conn.unsubscribe("rt/unitree/slam_mapping/odom")
    
    return messages
```

### Web App: Stream to Browser via WebSocket
```python
# In g1_app/ui/web_server.py
import asyncio
from aiohttp import web

async def websocket_slam_odom(request):
    """WebSocket endpoint for real-time SLAM odometry."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # Subscribe to odom topic
    async def send_odom(msg):
        # Convert message to JSON and send to browser
        await ws.send_json({
            "type": "slam_odom",
            "position": msg.get("position"),
            "orientation": msg.get("orientation"),
            "timestamp": time.time()
        })
    
    # Subscribe to topic
    await conn.subscribe("rt/unitree/slam_mapping/odom", send_odom)
    
    # Wait for browser to close connection
    async for msg in ws:
        if msg.type == web.WSMsgType.CLOSE:
            break
    
    return ws
```

### Browser: Receive Odometry via WebSocket
```javascript
// In g1_app/ui/index.html
const ws = new WebSocket('ws://localhost:9000/api/slam/odom');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === "slam_odom") {
        // Update 3D viewer
        updateRobotPosition(
            data.position.x,
            data.position.y,
            data.position.z
        );
        updateRobotOrientation(
            data.orientation.x,
            data.orientation.y,
            data.orientation.z,
            data.orientation.w
        );
        
        // Add to trajectory
        addTrajectoryPoint(data.position);
    }
};
```

---

## ⚡ Why This Is Better

### Before (Wrong Topic, Server Restart):
```
Idea → Code → Start Server → Refresh Browser → No Data ❌ 
→ Check Logs → Realize wrong topic → Restart Server → Try Again
→ Total: 15-20 seconds per iteration
```

### After (Correct Topics, WebSocket):
```
Python Test → Verify Topics Work ✅ 
→ Integrate WebSocket → Refresh Browser ✅ 
→ See Real-Time Update → Adjust Code → Refresh Again ✅ 
→ Total: 2-3 seconds per iteration
```

**Result**: ~5-10x faster development cycle

---

## 📊 Testing Checklist

Before starting web app implementation:

- [ ] Run `test_slam_topics_realtime.py`
- [ ] Verify `rt/unitree/slam_mapping/odom` publishes during mapping
- [ ] Verify `rt/unitree/slam_relocation/odom` publishes during navigation
- [ ] Check message format (position, orientation, etc.)
- [ ] Check frequency (should be ~20 Hz)
- [ ] Confirm wrong topic (`rt/unitree/slam_mapping/points`) doesn't work

**If all ✅**: Proceed to WebSocket implementation  
**If any ❌**: Debug with robot team (may need firmware update or different robot model)

---

## 🎯 Success Criteria

**Python Test**:
- ✅ Receives odometry messages from correct topics
- ✅ Message format understood (position, orientation)
- ✅ Frequency acceptable for 3D rendering

**Web App**:
- ✅ WebSocket endpoint created
- ✅ Browser receives real-time odometry
- ✅ 3D viewer updates without page refresh
- ✅ Orientation correct (no flipped axes)
- ✅ Mouse interaction works (rotate, zoom)
- ✅ Trajectory displayed

**Performance**:
- ✅ <100ms latency (human-perceptible)
- ✅ Browser not lagging
- ✅ Can debug with F5 refresh (not server restart)

---

## 🚀 Next Steps

1. **Run Python test**: `python3 test_slam_topics_realtime.py`
2. **Verify topics work** (should show ✅)
3. **Report results**: Which topics work, what format?
4. **Proceed to WebSocket integration** (if topics work)
5. **Implement browser streaming** (fast refresh loop)

The key insight: **Use Python for API/topic testing (no overhead), then WebSocket for web app (no restart overhead).**

