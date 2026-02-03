# G1 Arm Teaching Interface - Quick Start Guide

## 🦾 What is This?

A simple coordinate-based arm teaching interface for the Unitree G1 robot. Record and playback arm motions without needing AI/ML training - just capture waypoints and play them back!

## 🚀 Quick Start

### Windows:
```batch
START_ARM_TEACHING.bat
```

This will:
1. Start the web server on port 3000
2. Open your browser to the arm teaching interface
3. Connect to your G1 robot automatically

### Manual Start:
```bash
# Activate virtual environment
.venv\Scripts\activate

# Start server
python -m uvicorn g1_app.ui.web_server:app --host 127.0.0.1 --port 3000

# Open browser to:
http://localhost:3000/static/arm_teaching.html
```

## 📋 Features

### 1. Manual Joint Control
- **7 DOF Control**: Control all 7 joints of the arm
  - Shoulder Pitch, Roll, Yaw
  - Elbow
  - Wrist Roll, Pitch, Yaw
- **Real-time Sliders**: Adjust each joint angle with visual feedback
- **Live Robot Updates**: Send poses to robot in real-time
- **Read Current Pose**: Get actual joint angles from robot

### 2. Waypoint Recording
- **Manual Capture**: Click "Capture Waypoint" to save current pose
- **Continuous Recording**: Record smooth trajectories automatically
- **Multi-Arm Support**: Switch between left and right arms

### 3. Sequence Playback
- **Smooth Interpolation**: Robot moves smoothly between waypoints
- **Adjustable Speed**: Control playback speed (0.5x to 2x)
- **Safe Limits**: All joint angles are clamped to safe ranges

### 4. Save/Load Sequences
- **Export to JSON**: Save your taught motions to files
- **Import Sequences**: Load previously saved motions
- **Share Motions**: Transfer sequences between robots

## 🎮 How to Use

### Teaching a Simple Motion:

1. **Select Arm**:
   - Click "Left Arm" or "Right Arm" button

2. **Move to First Position**:
   - Adjust sliders to desired pose
   - Click "Send to Robot" to verify
   - Click "📍 Capture Waypoint"

3. **Add More Waypoints**:
   - Move sliders to next position
   - Click "📍 Capture Waypoint"
   - Repeat for all desired positions

4. **Play Back**:
   - Click "▶️ Play Sequence"
   - Watch robot execute the motion!

5. **Save Your Work**:
   - Click "💾 Save Sequence"
   - Enter a name (e.g., "button_push")
   - Download JSON file

### Recording Continuous Trajectories:

1. **Prepare Robot**:
   - Put robot arm in starting position

2. **Start Recording**:
   - Click "⏺️ Start Recording"
   - Manually move the robot arm (robot must be in damp mode)
   - Waypoints captured automatically every 500ms

3. **Stop and Play**:
   - Click "⏹️ Stop Recording"
   - Review waypoints in list
   - Click "▶️ Play Sequence"

## 🔧 Technical Details

### API Endpoints

Based on findings from [Sentdex's unitree_g1_vibes](https://github.com/Sentdex/unitree_g1_vibes):

```python
# Move arm to pose
POST /api/arm/move
{
    "arm": "left",  # or "right"
    "joints": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 7 joint angles in radians
    "speed": 1.0  # movement speed multiplier
}

# Read current pose
GET /api/arm/read?arm=left

# Play sequence
POST /api/arm/play_sequence
{
    "waypoints": [
        {"arm": "left", "joints": [...]},
        {"arm": "left", "joints": [...]}
    ],
    "speed": 1.0
}

# Get preset poses
GET /api/arm/presets?arm=left

# Move to preset
POST /api/arm/preset/button_push?arm=left&speed=1.0
```

### Joint Configuration

**Left Arm (Motor Indices 15-21):**
- Joint 0: Shoulder Pitch (-180° to 180°)
- Joint 1: Shoulder Roll (-180° to 180°)
- Joint 2: Shoulder Yaw (-180° to 180°)
- Joint 3: Elbow (0° to 180°)
- Joint 4: Wrist Roll (-180° to 180°)
- Joint 5: Wrist Pitch (-180° to 180°)
- Joint 6: Wrist Yaw (-180° to 180°)

**Right Arm (Motor Indices 22-28):** Same as left

### Communication Protocol

- **Topic**: `rt/arm_sdk` (from Unitree SDK2)
- **Message Type**: `LowCmd_` with joint commands
- **Update Rate**: 50 Hz (20ms intervals)
- **Special**: Motor 29 must have `q=1` to enable arm SDK

### Control Parameters

```python
# Joint command structure (per joint)
{
    "motor_index": 15-21 (left) or 22-28 (right),
    "q": 0.0,      # Position in radians
    "dq": 0.0,     # Velocity (usually 0 for position control)
    "tau": 0.0,    # Feed-forward torque
    "kp": 60.0,    # Position gain (stiffness: 20-80)
    "kd": 1.5      # Damping gain (0.5-3.0)
}
```

**Tuning Tips:**
- Higher `kp` (60-80): Stiffer, faster response, but can be jerky
- Lower `kp` (20-40): Smoother, more compliant, but slower
- Higher `kd` (2-3): More damping, reduces oscillation
- Lower `kd` (0.5-1): Less damping, can be bouncy

## 🎯 Example Use Cases

### Push a Button

1. **Preset Pose**: Use the built-in "button_push" preset
   ```javascript
   // Via API
   POST /api/arm/preset/button_push?arm=left&speed=1.0
   ```

2. **Custom Sequence**:
   - Waypoint 1: Arm at rest
   - Waypoint 2: Arm extended toward button
   - Waypoint 3: Arm pushed forward (button pressed)
   - Waypoint 4: Arm retracted
   - Waypoint 5: Back to rest

### Pick and Place

1. Record approach to object
2. Close gripper (separate control - not implemented yet)
3. Lift object
4. Move to destination
5. Lower object
6. Open gripper
7. Retract

### Wave Gesture

1. Start with arm down
2. Raise arm up
3. Move left
4. Move right (repeat 3-4 times)
5. Lower arm

## 🛡️ Safety Features

- **Joint Limits**: All angles clamped to safe ranges
- **Smooth Interpolation**: Gradual transitions between poses
- **Connection Status**: Visual indicator of robot connection
- **Error Handling**: Graceful failures with status logging

## 🐛 Troubleshooting

### "Disconnected from Robot"
- Check robot is powered on
- Verify network connection (robot IP: 192.168.86.3)
- Restart web server

### Arm Not Moving
- Verify robot is in correct FSM state (not zero-torque)
- Check connection status (green = connected)
- View status log for error messages
- Try "Read from Robot" to verify communication

### Jerky Movements
- Reduce `kp` gain (20-40 for smoother motion)
- Increase movement duration (slower speed)
- Add more waypoints for finer control

### Sequence Won't Play
- Ensure at least 2 waypoints captured
- Check all waypoints have valid joint angles
- Verify robot is connected
- Check status log for errors

## 📊 Status Log

The bottom panel shows real-time status messages:
- 🟢 **Green**: Success messages
- 🔴 **Red**: Error messages
- ⚪ **White**: Info messages

## 🔗 Related Pages

- **Main Dashboard**: http://localhost:3000
- **Original Controller**: http://localhost:3000/static/index.html
- **API Documentation**: http://localhost:3000/docs

## 📝 File Format

Saved sequences are JSON files:

```json
{
  "name": "button_push",
  "created": "2026-02-03T12:00:00Z",
  "waypoints": [
    {
      "id": 0,
      "arm": "left",
      "joints": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      "timestamp": "2026-02-03T12:00:01Z"
    },
    {
      "id": 1,
      "arm": "left",
      "joints": [0.6, 0.2, 0.0, 1.4, 0.0, -0.4, 0.0],
      "timestamp": "2026-02-03T12:00:02Z"
    }
  ]
}
```

## 🚧 Limitations (G1 Air)

Since you have a G1 Air (no Jetson NX):
- ✅ WebRTC wrapper handles communication (works!)
- ✅ Commands sent via datachannel (same as Android app)
- ❌ No direct DDS access (expected for G1 Air)
- ❌ Cannot run code on robot's PC (no SSH)

**This is normal** - your implementation uses the same WebRTC protocol as the Unitree Explore app, which is the correct approach for G1 Air models.

## 🎓 Credits

Based on research from:
- [Sentdex's unitree_g1_vibes](https://github.com/Sentdex/unitree_g1_vibes) - Arm control patterns
- Unitree SDK2 documentation - DDS topic structure
- Android APK reverse engineering - WebRTC protocol

## 📞 Support

If you encounter issues:
1. Check status log for error messages
2. Review browser console (F12) for JavaScript errors
3. Verify robot network connection
4. Check if you can control robot from Android app (confirms robot is working)

---

**Ready to teach your robot!** Start with simple 2-3 waypoint sequences and gradually build more complex motions. 🦾
