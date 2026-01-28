# Teaching Mode API Analysis

## Capture File Issue

The provided pcap file `teaching mode.pcapng` does not contain any IP traffic between the phone (192.168.137.220) and robot (192.168.137.164).

**Possible reasons:**
1. Capture was done on wrong network interface
2. WebRTC datachannel uses encrypted DTLS-SCTP which appears as UDP but encrypted
3. Traffic is relayed through TURN server instead of direct peer-to-peer
4. Capture filter excluded the relevant traffic

## What We Need to Find

Based on the SDK analysis and experimental code, we need to discover the **actual request/response format** for these APIs:

### 1. **API 7109: START_RECORD_ACTION** (Experimental)
**Purpose:** Begin recording arm motion for teach mode

**Expected Request:**
```json
{
  "api_id": 7109,
  "parameter": {}  // Possibly empty, or may need action metadata
}
```

**Unknown:**
- Does it require action name upfront?
- Any prerequisites (FSM state, arm state)?
- Response format

### 2. **API 7110: STOP_RECORD_ACTION** (Experimental)
**Purpose:** Stop recording without saving

**Expected Request:**
```json
{
  "api_id": 7110,
  "parameter": {}
}
```

### 3. **API 7111: SAVE_RECORDED_ACTION** (Experimental)
**Purpose:** Save the recorded motion with a name

**Expected Request:**
```json
{
  "api_id": 7111,
  "parameter": {
    "action_name": "my_custom_action"
  }
}
```

**Unknown:**
- Does it automatically stop recording first?
- What if no recording is in progress?

### 4. **API 7112: DELETE_ACTION** (Experimental)
**Purpose:** Delete a saved taught action

**Expected Request:**
```json
{
  "api_id": 7112,
  "parameter": {
    "action_name": "action_to_delete"
  }
}
```

## Documented APIs (From SDK)

### API 7107: GET_ACTION_LIST ✅
**Request:**
```json
{
  "api_id": 7107,
  "parameter": {}
}
```

**Response Format:** (estimated from documentation)
```json
{
  "preset_actions": [
    {"id": 11, "name": "two-hand kiss"},
    {"id": 99, "name": "release arm"}
  ],
  "custom_actions": [
    {"name": "wave_hello", "duration": 3.5},
    {"name": "pick_object", "duration": 5.2}
  ],
  "fsm_restrictions": {
    "500": ["all"],
    "501": ["all"],
    "801": ["mode_0", "mode_3"]
  }
}
```

### API 7108: EXECUTE_CUSTOM_ACTION ✅
**Request:**
```json
{
  "api_id": 7108,
  "parameter": {
    "action_name": "wave_hello"
  }
}
```

**Response:**
```json
{
  "error_code": 0  // 0 = success
}
```

**State Published During Playback** (`rt/arm/action/state` topic):
```json
{
  "holding": false,
  "id": 100,
  "name": "wave_hello"
}
```

## How to Capture Properly

To analyze the teaching mode APIs, capture traffic while using the Unitree Explore App:

```bash
# On robot (if accessible)
tcpdump -i any -w teach_mode_complete.pcap host 192.168.137.220

# Or on PC (mirrored port or WiFi monitor mode)
sudo tcpdump -i <interface> -w teach_mode.pcap 'host 192.168.137.220 or host 192.168.137.164'
```

**Steps to record in app:**
1. Connect to robot via app
2. Start packet capture
3. Enter teach mode
4. Start recording (note exact timestamp)
5. Move arms through desired motion
6. Stop recording (note timestamp)
7. Save with name (note timestamp)
8. Play back saved action (note timestamp)
9. Get action list to verify save (note timestamp)
10. Stop capture

Then analyze with:
```bash
wireshark teach_mode.pcap
# Filter: ip.addr == 192.168.137.164
# Look for HTTP/WebSocket/WebRTC datachannel payloads with JSON
```

## Alternative: Test Experimental APIs Directly

Since we've implemented the experimental APIs 7109-7112 in the web controller, we can test them directly:

1. Restart web server with new endpoints
2. Enter teach mode via web UI (SetBalanceMode(0) + RELEASE_ARM)
3. Try calling `/api/teach/start_recording`
4. Manually pose robot arms
5. Try calling `/api/teach/stop_recording` then `/api/teach/save_recording?action_name=test1`
6. Check server logs for robot responses
7. Try `/api/custom_action/robot_list` to see if action appears

**If APIs don't exist:**
- Robot will return error codes (likely 7400 or "unknown API")
- We'll know to use Android app for recording only
- Web controller remains useful for playback and control

**If APIs work:**
- We've discovered undocumented recording APIs
- Can implement full teach mode in web controller
- Document the exact request/response formats
