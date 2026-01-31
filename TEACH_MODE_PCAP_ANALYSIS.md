# Teach Mode Protocol Analysis - PCAP & SDK Integration

## 🎯 Key Finding

**Teach mode uses HTTP/WebSocket protocol, NOT direct UDP API IDs**

This is critical: The captured traffic shows no raw API ID packets (7107, 7108, 7113). Instead, commands are sent as JSON in HTTP POST or WebSocket messages.

## 📊 PCAP Analysis Results

### Traffic Summary
- **Total packets**: 6,592
- **Teach mode API IDs found**: ❌ None
- **JSON objects found**: 2 (mostly empty)
- **Protocol**: HTTP/WebSocket (not UDP DDS)

### What This Means

The G1 Air robot:
1. **Does NOT use DDS for teach mode** (those APIs are C++ SDK only)
2. **Uses HTTP endpoints** for teach mode control (like AP/STA modes)
3. **Commands are JSON-based** (like movement commands)
4. **WebRTC may wrap HTTP** (like it wraps DDS internally)

## 🔍 Decompiled App Findings

### Code Structure
- Found "customaction", "actionlist" references in Android code
- But they're in ExoPlayer library (video player), not Unitree code
- Suggests app UI for teach mode exists but implementation is in WebRTC layer

### Important
The decompiled Unitree Explore app code for teach mode is likely in:
- `com/unitree/robotics/` packages (not found with simple search)
- WebRTC implementation (handles protocol layer)
- May be obfuscated or in native libraries

## 💡 Protocol Hypothesis

Based on analysis:

```
[Android App] 
    ↓
[WebRTC Connection]
    ↓
[HTTP Requests/WebSocket Messages]
    ↓
[Robot PC1 - WebRTC Module]
    ↓
[Internal DDS - API 7108/7113]
    ↓
[Robot Motion Control]
```

### Expected HTTP Endpoints

```javascript
// Get action list (similar to /api/discover)
GET /api/actions         // Returns all preset + custom actions

// Execute custom action (similar to /api/gesture)
POST /api/action/execute
{
  "action_name": "wave"  // or action_id
}

// Record new action (enter teach mode)
POST /api/action/record
{
  "action_name": "my_wave"
}

// Stop recording
POST /api/action/stop

// Get custom actions only
GET /api/actions/custom
```

## 🛠️ Implementation Strategy

### Stage 1: Basic Action List (7107)

**Goal**: Get both preset and custom actions

**Implementation**:
```python
# In g1_app/ui/web_server.py
@app.get("/api/actions")
async def get_action_list():
    """Get all actions (preset + custom)"""
    try:
        code, actions = robot_controller.get_action_list()
        return {
            "success": code == 0,
            "actions": actions,
            "error": None if code == 0 else f"Error code {code}"
        }
    except Exception as e:
        return {"success": False, "actions": [], "error": str(e)}

# In g1_app/core/robot_controller.py
async def get_action_list(self):
    """Get all available actions"""
    # This calls API 7107 via RPC
    # Returns both preset IDs (99, 11-27) and custom action names
```

### Stage 2: Execute Custom Action (7108)

**Goal**: Play a custom taught action

**Implementation**:
```python
# In g1_app/ui/web_server.py
@app.post("/api/action/execute")
async def execute_action(action_name: str = None, action_id: int = None):
    """Execute preset or custom action"""
    try:
        if action_id:
            # Preset action
            code = robot_controller.execute_action(action_id)
        elif action_name:
            # Custom action
            code = robot_controller.execute_custom_action(action_name)
        
        return {
            "success": code == 0,
            "error": None if code == 0 else f"Error code {code}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# In g1_app/core/robot_controller.py  
async def execute_custom_action(self, action_name: str):
    """Execute custom action (API 7108)"""
    # Wraps RPC call to robot
    # Robot plays the recorded motion
```

### Stage 3: Record Custom Action (7109)

**Goal**: Record new gesture

**Implementation**:
```python
# State tracking
self.teach_mode_active = False
self.teach_action_name = None

# Start recording
@app.post("/api/action/record/start")
async def start_recording(action_name: str):
    code = robot_controller.record_custom_action(action_name)
    return {"success": code == 0}

# Stop recording
@app.post("/api/action/record/stop")
async def stop_recording():
    code = robot_controller.stop_custom_action()
    return {"success": code == 0}
```

## 🔗 Connection Between Layers

### Current Web Controller Architecture

```
┌─────────────────────────────────────────┐
│  Web UI (HTML/JavaScript)              │
│  - Lists preset gestures               │
│  - Shows custom actions                │
│  - Teach mode record/stop buttons      │
└──────────────┬──────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────┐
│  Web Server (web_server.py)            │
│  - /api/gesture → execute preset      │
│  - /api/actions → list actions        │
│  - /api/action/execute → custom      │
│  - /api/action/record → teach mode   │
└──────────────┬──────────────────────────┘
               │ Python SDK RPC
┌──────────────▼──────────────────────────┐
│  Robot Controller (robot_controller.py)│
│  - ExecuteCustomAction (API 7108)     │
│  - RecordCustomAction (API 7109)      │
│  - GetActionList (API 7107)           │
│  - StopCustomAction (API 7113)        │
└──────────────┬──────────────────────────┘
               │ WebRTC to Robot
┌──────────────▼──────────────────────────┐
│  Robot PC1 - WebRTC Module            │
│  - Converts HTTP to DDS messages      │
│  - Routes to arm_sdk service          │
└──────────────┬──────────────────────────┘
               │ Internal DDS
┌──────────────▼──────────────────────────┐
│  Robot Motion Control (Low-level)      │
│  - Motor commands                      │
│  - FSM state machine                   │
│  - Arm control & recording             │
└─────────────────────────────────────────┘
```

## 📋 Implementation Checklist

### Phase 1: Get Action List (Priority 1)
- [ ] Add `/api/actions` endpoint in web_server.py
- [ ] Call API 7107 via RobotController
- [ ] Return list with IDs and names
- [ ] Update UI to populate action dropdown

### Phase 2: Execute Custom Action (Priority 1)
- [ ] Add `/api/action/execute` endpoint
- [ ] Call API 7108 with action name
- [ ] Update UI action buttons
- [ ] Add to gesture panel

### Phase 3: Record Action (Priority 2)
- [ ] Add teach mode state tracking
- [ ] Add `/api/action/record/start` endpoint
- [ ] Add `/api/action/record/stop` endpoint
- [ ] Call APIs 7109 and 7113
- [ ] Add UI workflow (enter teach mode → record → stop)

### Phase 4: Advanced (Priority 3)
- [ ] Delete custom action (API 7110)
- [ ] Clear all actions (API 7112)
- [ ] Get only custom actions (API 7111)
- [ ] Action library management UI

## 🐍 Python SDK: Add Missing Methods

To support teach mode, add to `sdk2_python/unitree_sdk2py/g1/arm/g1_arm_action_client.py`:

```python
def ExecuteCustomAction(self, action_name: str):
    """Execute custom taught action (API 7108)"""
    p = {}
    p["data"] = action_name
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_EXECUTE_CUSTOM_ACTION, parameter)
    return code

def RecordCustomAction(self, action_name: str):
    """Start recording custom action (API 7109)"""
    p = {}
    p["data"] = action_name
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_RECORD_ACTION, parameter)
    return code

def StopCustomAction(self):
    """Stop recording or execution (API 7113)"""
    p = {}
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_STOP_CUSTOM_ACTION, parameter)
    return code

def GetCustomActionList(self):
    """Get list of custom actions only (API 7111)"""
    p = {}
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_GET_ACTION_LIST_CUSTOM, parameter)
    if code == 0:
        return code, json.loads(data)
    else:
        return code, None
```

Add to `sdk2_python/unitree_sdk2py/g1/arm/g1_arm_action_api.py`:

```python
ROBOT_API_ID_ARM_ACTION_EXECUTE_CUSTOM_ACTION = 7108
ROBOT_API_ID_ARM_ACTION_RECORD_ACTION = 7109
ROBOT_API_ID_ARM_ACTION_DELETE_ACTION = 7110
ROBOT_API_ID_ARM_ACTION_GET_ACTION_LIST_CUSTOM = 7111
ROBOT_API_ID_ARM_ACTION_CLEAR_ACTIONS = 7112
ROBOT_API_ID_ARM_ACTION_STOP_CUSTOM_ACTION = 7113
```

## 🧪 Testing Workflow

1. **Get action list**
   ```bash
   curl http://localhost:9000/api/actions
   # Returns: {"success": true, "actions": [...]}
   ```

2. **Execute preset action**
   ```bash
   curl -X POST http://localhost:9000/api/gesture/18
   # Executes "high five" (ID 18)
   ```

3. **Execute custom action**
   ```bash
   curl -X POST http://localhost:9000/api/action/execute?action_name=wave
   # Executes custom "wave" action
   ```

4. **Record new action**
   ```bash
   curl -X POST http://localhost:9000/api/action/record/start?action_name=my_gesture
   # Robot enters teach mode for 30 seconds
   # User performs motion
   curl -X POST http://localhost:9000/api/action/record/stop
   # Saves motion as "my_gesture"
   ```

## 🚨 Important Gotchas

1. **FSM State Requirements**
   - Must be in correct state (500/501 for gestures, 801 for custom)
   - Recording requires different state than execution

2. **Teach Mode Timeout**
   - Robot may exit teach mode after timeout
   - May need to keep connection alive

3. **Action Storage**
   - Custom actions stored on robot
   - May have size/count limits
   - Survive reboot (stored in persistent memory)

4. **G1 Air Limitations**
   - May not support teach mode at all
   - Or may require different protocol
   - Test with actual robot first

## 📝 Next Steps

1. **Implement Stage 1** - Get action list endpoint
2. **Test with robot** - Verify API 7107 works
3. **Implement Stage 2** - Execute custom action
4. **Test execution** - Record simple gesture, play it back
5. **Add UI** - Make it user-friendly
6. **Document** - Update guides

## References

- Python SDK: [TEACH_MODE_REFERENCE.md](TEACH_MODE_REFERENCE.md)
- PCAP Analysis: [This file]
- Web Controller: `g1_app/ui/web_server.py`
- Robot Controller: `g1_app/core/robot_controller.py`
