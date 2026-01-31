# Session Summary: STUN Port Discovery & Teaching Mode UI Implementation

## Date: January 30, 2026

### Overview
Completed STUN protocol analysis to understand port discovery mechanism, extracted encryption credentials, and fully implemented delete/rename buttons in the teaching mode web UI.

---

## Part 1: STUN Port Discovery Analysis

### Findings
- **STUN Protocol RFC 5389**: Identified STUN magic cookie (0x2112A442) in port 51639 traffic
- **Total STUN Packets**: 174 packets in PCAPdroid_30_Jan_18_26_35.pcap
- **Port Discovery Mechanism**: XOR-MAPPED-ADDRESS attribute reveals external port mapping
- **Discovered Ports**:
  - Port 51639: STUN server on robot (192.168.86.3:51639)
  - Port 57006: Teaching protocol UDP port (192.168.86.6:57006)
  - Port 45559: Alternative port (192.168.123.161:45559)

### STUN Credentials Extracted
```
Primary Username: n7Px:iq2R (hex: 6e3750783a69713252)
Response Username: iq2R:n7Px (reversed)
Authentication: HMAC-SHA1 via MESSAGE-INTEGRITY attribute
Fingerprint: CRC32 via FINGERPRINT attribute
```

### STUN Packet Flow
```
[1] Android Binding Request
    FROM: 10.215.173.1:34052
    TO: 192.168.86.3:51639
    USERNAME: n7Px:iq2R
    MESSAGE-INTEGRITY: HMAC-SHA1 signed
    
[2] Robot Binding Response
    FROM: 192.168.86.3:51639
    TO: 10.215.173.1:34052
    XOR-MAPPED-ADDRESS: 192.168.86.6:57006
    ← Tells Android which port to use for teaching protocol
    
[3-174] Pattern repeats 174 times (NAT keepalive/sync)
```

### Created Scripts
- **analyze_stun_port_discovery.py**: RFC 5389 STUN parser with XOR-MAPPED-ADDRESS extraction
- **decrypt_with_stun_credentials.py**: STUN credential extraction and key derivation
- **test_stun_keys_on_payloads.py**: Test STUN-derived keys on teaching protocol

---

## Part 2: Encryption Key Analysis

### Derived Keys from STUN Username
Created 8 potential encryption keys from `n7Px:iq2R`:

| Method | Key Length | Hex Value | Status |
|--------|-----------|-----------|--------|
| Direct ASCII | 9 bytes | `6e3750783a69713252` | ✓ Tested |
| HMAC-SHA1 (empty key) | 20 bytes | `872a83c74b2983d0...` | ✓ Tested |
| HMAC-SHA1 (self-keyed) | 20 bytes | `c985e775994233047...` | ✓ Tested |
| HMAC-SHA1 ('unitree' key) | 20 bytes | `e278cc4b524fcd33...` | ✓ Tested |
| SHA1(username) | 20 bytes | `a439021cdf370de99...` | ✓ Tested |
| SHA256(username) | 32 bytes | `59626fb5894cd61e0...` | ✓ Tested |
| AES-128 from HMAC | 16 bytes | `c985e775994233047...` | ✓ Tested |
| MD5(username) | 16 bytes | `82df3b3e0842cf157...` | ✓ Tested |

### Decryption Results
- Tested all 8 keys on actual encrypted protocol payloads (port 51639)
- XOR results show repeating key patterns, confirming payload encryption exists
- Neither known keys (UniPwn AES, FMX Blowfish) nor STUN credentials matched plaintext
- **Conclusion**: Teaching protocol likely uses different/session-specific encryption key

---

## Part 3: Web UI Implementation

### Changes to teach_mode.html

#### 1. Added Rename Button to Action List
```html
<div class="action-buttons">
    <button class="success" onclick="playAction('${action}')">▶ Play</button>
    <button class="info" onclick="renameAction('${action}')">✎ Rename</button>
    <button class="danger" onclick="deleteAction('${action}')">🗑 Delete</button>
</div>
```

#### 2. Added Info Button CSS Style
```css
button.info {
    background: #3b82f6;
}

button.info:hover:not(:disabled) {
    background: #2563eb;
}
```

#### 3. Added renameAction() JavaScript Function
```javascript
async function renameAction(oldName) {
    const newName = prompt(`Rename action "${oldName}" to:`, oldName);
    if (!newName || newName === oldName) return;
    if (newName.trim().length === 0) {
        showMessage('Action name cannot be empty', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/teach/rename_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_name: oldName, new_name: newName })
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage(`✓ Renamed action: ${oldName} → ${newName}`, 'success');
            loadActionList();
        } else {
            showMessage('Failed to rename action: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showMessage('Error renaming action: ' + error.message, 'error');
    }
}
```

### Changes to web_server.py

#### Added rename_action Endpoint
```python
@app.post("/api/teach/rename_action")
async def rename_action_endpoint(old_name: str, new_name: str):
    """EXPERIMENTAL: Rename saved action (API 7113)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    if not old_name or not new_name:
        return {"success": False, "error": "Action names cannot be empty"}
    
    try:
        result = await robot.executor.rename_action(old_name, new_name)
        logger.info(f"Rename action result: {result}")
        return {
            "success": True,
            "message": f"Action '{old_name}' renamed to '{new_name}' (experimental API)",
            "data": result
        }
    except Exception as e:
        logger.error(f"Rename action failed: {e}")
        return {"success": False, "error": str(e)}
```

### Changes to command_executor.py

#### Added rename_action Method
```python
async def rename_action(self, old_name: str, new_name: str) -> dict:
    """
    EXPERIMENTAL: Rename a saved action
    
    Args:
        old_name: Current name of the action
        new_name: New name for the action
        
    Returns:
        Command payload
    """
    payload = {
        "api_id": ArmAPI.RENAME_ACTION,
        "parameter": json.dumps({"old_name": old_name, "new_name": new_name})
    }
    logger.info(f"EXPERIMENTAL: Renaming action '{old_name}' to '{new_name}' (API 7113)")
    return await self._send_command(payload, service=Service.ARM)
```

### Changes to constants.py

#### Updated ArmAPI Constants
```python
class ArmAPI(IntEnum):
    """Arm action client API IDs"""
    EXECUTE_ACTION = 7106           # Execute pre-programmed gesture
    GET_ACTION_LIST = 7107          # Retrieve available gestures
    EXECUTE_CUSTOM_ACTION = 7108    # Play teach mode recording
    
    # Undocumented APIs (gaps in numbering - likely recording APIs)
    START_RECORD_ACTION = 7109      # EXPERIMENTAL: Start recording teach action
    STOP_RECORD_ACTION = 7110       # EXPERIMENTAL: Stop recording
    SAVE_RECORDED_ACTION = 7111     # EXPERIMENTAL: Save recording with name
    DELETE_ACTION = 7112            # EXPERIMENTAL: Delete saved action
    RENAME_ACTION = 7113            # EXPERIMENTAL: Rename saved action ← NEW
    
    STOP_CUSTOM_ACTION = 7114       # Stop teach playback
```

---

## Implementation Status

### ✅ Completed Tasks
1. STUN protocol analysis (RFC 5389)
   - Port discovery mechanism identified
   - 174 STUN packets analyzed
   - External port mapping revealed (57006)

2. STUN credential extraction
   - Username: n7Px:iq2R extracted from STUN packets
   - 8 encryption keys derived from credentials
   - Testing on teaching protocol payloads completed

3. Web UI delete/rename implementation
   - Delete button already existed in UI
   - Added Rename button with `✎` icon
   - Added info button CSS styling
   - Implemented renameAction() JavaScript function
   - Added /api/teach/rename_action endpoint
   - Added CommandExecutor.rename_action() method
   - Added ArmAPI.RENAME_ACTION constant (7113)

### ⏳ Pending Tasks
1. Physical robot testing (requires G1_6937 connection)
2. Decrypt teaching protocol (requires finding correct encryption key)
3. Validate FSM state machine compliance for delete/rename
4. Test action sync with Android app

---

## API Summary

### Teaching Mode Actions
| Operation | UDP Cmd | API ID | Status |
|-----------|---------|--------|--------|
| List Actions | 0x1A | 7107 | ✅ Implemented |
| Record Start | ? | 7109 | Implemented |
| Record Stop | ? | 7110 | Implemented |
| Save Action | ? | 7111 | Implemented |
| **Delete Action** | **0x42** | **7112** | **✅ Implemented** |
| **Rename Action** | **0x43** | **7113** | **✅ NEW - Implemented** |
| Stop Playback | ? | 7114 | Implemented |

---

## Protocol Architecture (Updated)

```
Layer 1: Network Discovery
  ├─ STUN RFC 5389 (port 51639)
  │  ├─ Binding Request/Response
  │  ├─ XOR-MAPPED-ADDRESS for port mapping
  │  └─ USERNAME auth: n7Px:iq2R
  │
Layer 2: Teaching Protocol (UDP port 57006/51639)
  ├─ 0x1A: Get/List Actions
  ├─ 0x42: Delete Action (encrypted)
  ├─ 0x43: Rename Action (encrypted)
  ├─ 0x09-0x0F: Other teaching commands
  └─ [Encryption: Unknown key derivation]

Layer 3: Web API
  ├─ /api/teach/action_list (GET)
  ├─ /api/teach/delete_action (POST) - API 7112
  └─ /api/teach/rename_action (POST) - API 7113 ← NEW
```

---

## Files Modified

### Core Implementation
- [g1_app/ui/teach_mode.html](g1_app/ui/teach_mode.html) - UI: Added rename button & function
- [g1_app/ui/web_server.py](g1_app/ui/web_server.py) - Backend: Added rename endpoint
- [g1_app/core/command_executor.py](g1_app/core/command_executor.py) - Executor: Added rename method
- [g1_app/api/constants.py](g1_app/api/constants.py) - Constants: Added RENAME_ACTION

### Analysis Scripts (New)
- analyze_stun_port_discovery.py - STUN RFC 5389 parser
- decrypt_with_stun_credentials.py - STUN credential extraction
- test_stun_keys_on_payloads.py - Key testing on payloads
- debug_pcap_content.py - PCAP packet inspection
- find_teaching_on_port.py - Teaching protocol port finder
- debug_stun_packet.py - STUN packet structure debug
- find_042_043.py - Command ID search

---

## Next Steps

1. **Physical Testing** (requires robot connection)
   ```
   1. Connect to G1_6937
   2. Start teach mode
   3. Record action → rename it → test UI buttons
   4. Verify FSM compliance (teaching mode state)
   5. Check action sync with Android app
   ```

2. **Encryption Investigation**
   - Analyze teaching protocol encryption key derivation
   - Test if STUN username is used in cipher initialization
   - Compare with UniPwn/FMX documented methods

3. **Documentation**
   - Update API reference with RENAME_ACTION (7113)
   - Document STUN port discovery flow
   - Add teaching mode security notes

---

## Files for Potential Cleanup
- search_042_043.py (old - binary search already replaced)
- xor_brute_force.py (old - keys tested)
- known_plaintext_attack.py (old - no matches)
- unitree_encryption_keys.py (old - keys tested)

---

**Session Status**: ✅ COMPLETE - All UI implementation done, ready for robot testing
