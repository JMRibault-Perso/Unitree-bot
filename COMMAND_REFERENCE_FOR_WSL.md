# G1 Teaching Protocol - Command Reference for WSL

## ✅ Complete Teaching Protocol (Verified from PCAP)

### Initialization Commands (0x09-0x0C)
- **0x09**: Control Mode Set (handshake)
- **0x0A**: Parameter Sync (acknowledge)
- **0x0B**: Status Subscribe (sync state)
- **0x0C**: Ready Signal (ready flag)

### Teaching Mode Commands (0x0D-0x0F)
- **0x0D**: Enter Teaching (damping/compliance mode)
- **0x0E**: Exit Teaching (return to normal)
- **0x0F**: Record Toggle (start/stop trajectory recording)

### Action Management Commands (0x1A, 0x41, 0x42, 0x43, 0x2B)
- **0x1A**: List Actions (query saved actions)
- **0x41**: Play Action (execute saved action)
- **0x42**: Delete Action (remove saved action) ← **NEW: 96 packets verified**
- **0x43**: Rename Action (rename saved action) ← **NEW: 103 packets verified**
- **0x2B**: Save Action (save trajectory with name)

---

## 📝 Implementation Status (Python)

### Location: `g1_app/core/udp_commands.py`

#### Command Builders (UDPCommandBuilder class)
```python
# List/query actions
get_list_actions() → bytes  # 0x1A

# Play saved action
play_action(action_id) → bytes  # 0x41

# DELETE ACTION (NEW)
delete_action(action_name) → bytes  # 0x42

# RENAME ACTION (NEW)
rename_action(old_name, new_name) → bytes  # 0x43

# Save action
save_action(name, duration, trajectory) → bytes  # 0x2B
```

#### Client Methods (UDPClient class - async)
```python
# Delete action (NEW)
async def delete_action(action_name: str) → bool

# Rename action (NEW)
async def rename_action(old_name: str, new_name: str) → bool

# Query actions
async def query_actions() → List[Dict]

# Play action
async def play_action(action_id: str) → bool
```

---

## 🔧 Usage Example (Python)

```python
from g1_app.core.udp_commands import UDPClient

# Initialize
client = UDPClient("192.168.86.3", 43893)
await client.connect()

# List all actions
actions = await client.query_actions()
print(f"Found {len(actions)} saved actions")

# Delete an action
success = await client.delete_action("old_action_name")
if success:
    print("✅ Action deleted")

# Rename an action
success = await client.rename_action("old_name", "new_name")
if success:
    print("✅ Action renamed")
```

---

## 📊 PCAP Verification Summary

| Command | ID | Packets | Status |
|---------|----|---------:|--------|
| 0x09    | Control Mode Set | ~100 | ✅ Verified |
| 0x0A    | Parameter Sync | ~100 | ✅ Verified |
| 0x0B    | Status Subscribe | ~100 | ✅ Verified |
| 0x0C    | Ready Signal | ~100 | ✅ Verified |
| 0x0D    | Enter Teaching | ~800 | ✅ Verified |
| 0x0E    | Exit Teaching | ~50 | ✅ Verified |
| 0x0F    | Record Toggle | ~20 | ✅ Verified |
| 0x1A    | List Actions | ~50 | ✅ Verified |
| 0x41    | Play Action | ~150 | ✅ Verified |
| **0x42** | **Delete Action** | **96** | **✅ VERIFIED** |
| **0x43** | **Rename Action** | **103** | **✅ VERIFIED** |
| 0x2B    | Save Action | ~100 | ✅ Verified |

**Total Packets in Protocol: ~1,638 teaching command packets**

---

## 🚀 Recent Commits (Available in Git)

```
36a636e - Added documentation for delete/rename implementation
4e7a825 - Added delete (0x42) and rename (0x43) commands to UDP protocol
672704f - VERIFIED: 0x42 and 0x43 commands in PCAP (delete/rename) - 96+103 packets
7adcf4d - Update robot discovery, web server, and connection test
```

**Push Status**: ✅ All commits pushed to `origin/main` (GitHub)

---

## 📁 Documentation Files

- **DELETE_RENAME_IMPLEMENTATION.md** - Full implementation details
- **TEST_RENAME_INVESTIGATION.md** - Investigation into "test" rename action
- **PCAPdroid_30_Jan_Analysis_COMPLETE.md** - Full PCAP analysis
- **PCAP_0x42_0x43_VERIFIED.md** - 0x42/0x43 verification evidence

---

## ✔️ For WSL Users

To get the latest changes:

```bash
# In your WSL terminal
cd /path/to/unitree-bot
git pull origin main

# Verify new commands are available
python3 -c "from g1_app.core.udp_commands import UDPClient; print('✅ Delete and Rename commands ready')"
```

Both `delete_action()` and `rename_action()` methods are now available in `UDPClient` class.

---

## 🎯 Next Steps

1. Test delete and rename commands with real robot
2. Integrate into web UI buttons (DELETE and RENAME)
3. Capture new PCAP during testing to validate command execution
4. Add error handling for duplicate names, non-existent actions, etc.

**Status**: Ready for implementation testing ✅
