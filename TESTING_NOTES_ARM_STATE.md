# Testing Notes: Arm State Reading Implementation

## What Was Changed

### robot_controller.py
1. **Added `_subscribe_to_lowstate()` method** (line 246-271)
   - Subscribes to `rt/lowstate` topic for motor position data
   - Caches data in `self.conn.datachannel.pub_sub._last_lowstate`
   - Logs when first lowstate received with motor count

2. **Implemented `request_arm_state()` method** (line 850-906)
   - Was previously a stub returning None
   - Now reads from cached lowstate data
   - Extracts motor positions: left arm (motors 15-21), right arm (motors 22-28)
   - Returns `{'joints': [7 float values in radians]}`

3. **Added debug logging** throughout to trace:
   - When lowstate subscription starts
   - When first lowstate data arrives
   - What data structure is received
   - Success/failure of arm position extraction

## How to Test in WSL

### Prerequisites
- Robot must be connected via WebRTC
- Robot must be publishing `rt/lowstate` topic (EDU models with Jetson NX only)

### Test Method 1: Via Web UI (Recommended)
```bash
cd /path/to/Unitree-bot
python -m uvicorn g1_app.ui.web_server:app --host 127.0.0.1 --port 8001 --reload
```

Then:
1. Open browser to `http://127.0.0.1:8001`
2. Connect to robot (192.168.86.11)
3. Navigate to "Teach Arm" screen
4. Click "Capture Pose" button

**Expected Logs (Success):**
```
✅ Subscribed to rt/lowstate for arm position reading
📖 Started caching rt/lowstate for arm reads (29 motors)
📖 Reading left arm state from rt/lowstate...
✅ Read left arm state: [0.123, -0.456, ...]
```

**Expected Logs (If rt/lowstate not published):**
```
✅ Subscribed to rt/lowstate for arm position reading
(no further logs about lowstate)
📖 Reading left arm state from rt/lowstate...
❌ rt/lowstate not cached yet - waiting for first message
```

### Test Method 2: Standalone Script
```bash
python test_fsm_query.py
```

This verifies WebRTC connection works and can receive API responses. If this works but lowstate doesn't, it means the G1 robot doesn't publish `rt/lowstate`.

## Known Issues

### G1 Air vs G1 EDU
- **G1 Air** (no Jetson NX): May not publish `rt/lowstate` topic
- **G1 EDU** (with Jetson NX): Should publish all SDK topics including `rt/lowstate`

If your G1 doesn't publish lowstate:
- Check robot model (Air vs EDU)
- Check if "SDK Mode" needs enabling in Unitree app
- May need alternative approach (reverse-engineer Android app's method)

### Alternative Topics to Try
If `rt/lowstate` doesn't work, try subscribing to:
- `rt/lf/lowstate` - GO2 uses this variant
- `rt/arm_state` - Possible G1-specific topic
- Check what topics ARE being published with a topic listener

## Data Structure

### LowState_ Message (Expected)
```python
{
    'data': {
        'motor_state': [
            {
                'q': 0.123,      # Position (radians)
                'dq': 0.0,       # Velocity
                'tau': 0.0,      # Torque
                'temperature': 30
            },
            # ... 29 motors total
        ],
        'imu_state': { ... },
        'battery': { ... }
    }
}
```

### Arm Motor Indices
- **Left arm**: motors 15-21 (7 DOF)
- **Right arm**: motors 22-28 (7 DOF)

## Debugging Commands

### Check what topics are being published:
Add this subscription in robot_controller.py temporarily:
```python
def log_all_messages(data):
    print(f"📨 Topic message: {list(data.keys())}")

self.conn.datachannel.pub_sub.subscribe("#", log_all_messages)  # Wildcard
```

### Check WebRTC connection health:
```python
# In test_fsm_query.py, add after connection:
print(f"DataChannel state: {conn.datachannel.pub_sub}")
print(f"Available methods: {dir(conn.datachannel.pub_sub)}")
```

## Next Steps If rt/lowstate Doesn't Exist

1. **Capture all topics** being published during arm movement
2. **Find alternative topic** that contains arm positions
3. **Reverse-engineer Android app** to see what it subscribes to
4. **Contact Unitree support** to ask about G1 Air SDK limitations

## Files Modified
- `g1_app/core/robot_controller.py` - Main implementation
- `test_fsm_query.py` - Test script with correct IP

## Commit Hash
`3fb3ce1` - "Implement arm state reading via rt/lowstate topic"
