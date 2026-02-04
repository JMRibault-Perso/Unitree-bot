# Teach Mode Recording Implementation Plan

## Overview
The G1 robot supports **full teach mode functionality** via WebRTC APIs:

**Available APIs:**
- **7107**: GetActionList - Retrieve all custom actions stored on robot
- **7108**: ExecuteCustomAction - Play back a custom action by name
- **7109**: StartRecordAction - Begin recording arm movements
- **7110**: StopRecordAction - Stop recording without saving
- **7111**: SaveRecordedAction - Save recording with a name
- **7112**: DeleteAction - Remove a custom action
- **7113**: StopCustomAction - Emergency stop during playback
- **7114**: RenameAction - Rename an existing action

**How it works:**
1. Actions are recorded and stored **on the robot itself**
2. Recording captures arm joint trajectories at ~50Hz
3. Playback executes the stored trajectory
4. Actions persist across robot reboots
5. Actions can be accessed from both Android app and web controller

## Architecture

### Backend Components Implemented ✅

**`g1_app/api/arm_api.py`**
- Full teach mode API implementation (7107-7114)
- WebRTC request/response handling
- Error handling and validation

**`g1_app/ui/teach_mode.html`**
- Complete teach mode user interface
- Record, play, rename, delete actions
- Real-time status updates

### Current Implementation Status

#### 1. Robot Controller Integration

Add to `g1_app/core/robot_controller.py`:

```python
from .teach_mode_recorder import TeachModeRecorder

class RobotController:
    def __init__(self):
        # ... existing code ...
        self.recorder = TeachModeRecorder()
        self.lowstate_subscriber = None  # Subscribe to rt/lowstate
    
    async def start_teach_recording(self, action_name: str) -> dict:
        """
        Start recording custom action
        
        Steps:
        1. Call SetBalanceMode(0) → FSM 501
        2. Execute RELEASE_ARM gesture (99)
        3. Subscribe to rt/lowstate topic
        4. Start recorder.start_recording(action_name)
        5. In state callback, call recorder.record_snapshot(motor_positions)
        """
        pass
    
    async def stop_teach_recording(self, action_name: str) -> dict:
        """
        Stop recording and save
        
        Steps:
        1. recorder.stop_recording(action_name)
        2. Unsubscribe from rt/lowstate
        3. Return to FSM 500 (LOCK_STAND)
        """
        pass
    
    async def playback_local_recording(self, action_name: str) -> dict:
        """
        Play back a locally recorded action using low-level motor commands
        
        Steps:
        1. Load recording from recorder.load_recording(action_name)
        2. Subscribe to rt/lowcmd topic
        3. Iterate through snapshots and send motor position commands
        4. Use kp/kd gains for smooth interpolation
        """
        pass
```

#### 2. Web Server Endpoints

Add to `g1_app/ui/web_server.py`:

```python
@app.post("/api/teach/start_recording")
async def start_teach_recording(action_name: str):
    """Start recording a new custom action"""
    result = await robot.start_teach_recording(action_name)
    return result

@app.post("/api/teach/stop_recording")
async def stop_teach_recording(action_name: str):
    """Stop recording and save"""
    result = await robot.stop_teach_recording(action_name)
    return result

@app.post("/api/teach/cancel_recording")
async def cancel_teach_recording():
    """Cancel current recording without saving"""
    robot.recorder.cancel_recording()
    return {"success": True}

@app.get("/api/teach/status")
async def get_teach_status():
    """Get current recording status"""
    return {
        "is_recording": robot.recorder.is_recording,
        "snapshot_count": len(robot.recorder.snapshots) if robot.recorder.is_recording else 0,
        "duration": time.time() - robot.recorder.record_start_time if robot.recorder.is_recording else 0
    }

@app.get("/api/teach/recordings")
async def list_local_recordings():
    """List locally recorded custom actions"""
    recordings = robot.recorder.list_recordings()
    return {"success": True, "recordings": recordings}

@app.post("/api/teach/playback")
async def playback_local_recording(action_name: str):
    """Play back a locally recorded action"""
    result = await robot.playback_local_recording(action_name)
    return result
```

#### 3. Frontend UI Updates

Update `g1_app/ui/index.html` teach mode section:

```html
<!-- Recording Controls -->
<div style="margin-bottom: 20px;">
    <input type="text" id="recordingName" placeholder="Action name" />
    <button id="recordBtn" onclick="toggleRecording()">🔴 Start Recording</button>
    <div id="recordingStatus">Not recording</div>
</div>

<!-- Recorded Actions List -->
<div id="localRecordingsList"></div>

<script>
let isRecording = false;

async function toggleRecording() {
    const btn = document.getElementById('recordBtn');
    const nameInput = document.getElementById('recordingName');
    
    if (isRecording) {
        // Stop recording
        const response = await fetch(`/api/teach/stop_recording?action_name=${nameInput.value}`, {method: 'POST'});
        const result = await response.json();
        if (result.success) {
            isRecording = false;
            btn.textContent = '🔴 Start Recording';
            loadLocalRecordings();
        }
    } else {
        // Start recording
        if (!nameInput.value) {
            alert('Enter action name first');
            return;
        }
        const response = await fetch(`/api/teach/start_recording?action_name=${nameInput.value}`, {method: 'POST'});
        const result = await response.json();
        if (result.success) {
            isRecording = true;
            btn.textContent = '⏹️ Stop Recording';
            updateRecordingStatus();  // Poll for updates
        }
    }
}

async function updateRecordingStatus() {
    if (!isRecording) return;
    
    const response = await fetch('/api/teach/status');
    const status = await response.json();
    document.getElementById('recordingStatus').textContent = 
        `Recording: ${status.snapshot_count} samples, ${status.duration.toFixed(1)}s`;
    
    setTimeout(updateRecordingStatus, 200);  // Update 5x/sec
}

async function loadLocalRecordings() {
    const response = await fetch('/api/teach/recordings');
    const data = await response.json();
    // Render list...
}

async function playLocalRecording(name) {
    const response = await fetch(`/api/teach/playback?action_name=${name}`, {method: 'POST'});
    // ...
}
</script>
```

## Implementation Priority

**Phase 1: Basic Recording** (Recommended to start here)
1. ✅ Create `TeachModeRecorder` class (DONE)
2. Integrate into `RobotController`
3. Add `/api/teach/start_recording` and `/api/teach/stop_recording` endpoints
4. Add UI buttons for start/stop
5. Subscribe to `rt/lowstate` during recording
6. Test: Can we successfully record arm positions?

**Phase 2: Playback**
1. Implement `playback_local_recording()` using low-level motor commands
2. Add `/api/teach/playback` endpoint
3. Test: Can we replay recorded trajectories smoothly?

**Phase 3: Management**
1. Add list/delete/rename endpoints
2. Add UI for managing recordings
3. Show recording metadata (duration, sample count, etc.)

## Key Technical Details

### Motor Position Recording
- Subscribe to `rt/lowstate` topic (DDS)
- Extract motor positions array (29 motors total)
- Record indices 15-28 (14 arm joints)
- Store at ~50 Hz sampling rate

### Playback via Low-Level Commands
- Publish to `rt/lowcmd` topic (DDS)
- Set motor positions with appropriate kp/kd gains
- Interpolate between snapshots for smooth motion
- Safety: Apply torque limits based on motor type (GearboxS: 17Nm)

### Storage Format
```json
{
  "name": "wave_custom",
  "created_at": 1706140800.0,
  "duration": 3.5,
  "sample_rate": 50.2,
  "snapshots": [
    {
      "timestamp": 0.0,
      "positions": {
        "left_shoulder_pitch": 0.1,
        "left_shoulder_roll": 0.2,
        ...
      }
    },
    ...
  ]
}
```

## Limitations

1. **Local recordings only**: Android app recordings use proprietary format stored on robot
2. **No DDS on G1 Air**: Recording requires subscribing to `rt/lowstate` (DDS topic) - won't work on G1 Air
3. **Low-level playback**: Recorded actions play via motor commands, not high-level gesture API
4. **Safety**: Need to verify balance is maintained during playback
5. **Compatibility**: Local recordings won't transfer to Android app

## Alternative: Android App Integration

If local recording doesn't work, would need to:
1. Reverse-engineer Android app's recording protocol
2. Implement HTTP/WebSocket endpoints that mimic app behavior
3. Store recordings in robot's internal filesystem (requires SSH access)

This is significantly more complex and requires understanding the proprietary protocol.
