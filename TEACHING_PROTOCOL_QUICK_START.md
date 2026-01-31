# 🚀 Teaching Mode Protocol - Quick Implementation Guide

**Status**: ✅ Complete & Ready for Testing  
**Based on**: PCAP analysis of 5,258 packets from Android app

---

## ⚡ Quick Reference - All 6 Commands

### Initialization (Required First)
```
Cmd 0x09 → Cmd 0x0A → Cmd 0x0B → Cmd 0x0C → [THEN Teaching Mode]
```

### Teaching Workflow
```
0x1A (List)    → Get all saved actions
0x0D (Enter)   → Enable zero-gravity damping mode
0x0F (Record)  → Start/stop trajectory recording
0x2B (Save)    → Persist action to memory
0x41 (Play)    → Execute saved action
0x0E (Exit)    → Return to normal control
```

---

## 📦 Packet Builder Template

```python
import socket
import struct
import zlib

class TeachModePacket:
    ROBOT_IP = "192.168.86.3"  # Discover via SSDP
    ROBOT_PORT = 49504
    
    def __init__(self):
        self.sequence = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def build(self, cmd_id, payload):
        """Build complete packet: Header(13) + Payload(N) + CRC(4)"""
        pkt = bytearray()
        pkt.extend(b'\x17\xfe\xfd\x00\x01\x00')  # Type + magic + flags
        pkt.extend(struct.pack('>H', self.sequence))  # Sequence
        pkt.extend(b'\x00\x00\x00\x01')  # Reserved
        pkt.append(cmd_id)
        pkt.extend(struct.pack('>H', len(payload)))  # Payload length
        pkt.extend(payload)
        
        # CRC32
        crc = zlib.crc32(pkt) & 0xFFFFFFFF
        pkt.extend(struct.pack('>I', crc))
        
        self.sequence += 1
        return bytes(pkt)
    
    def send(self, cmd_id, payload):
        """Send packet to robot"""
        packet = self.build(cmd_id, payload)
        self.socket.sendto(packet, (self.ROBOT_IP, self.ROBOT_PORT))
        return packet
```

---

## 🎯 Command Implementations

### 1️⃣ List Teaching Actions (0x1A)
```python
def list_actions(self):
    """Get all saved teaching actions - RETURNS: 233B response"""
    payload = bytearray(44)  # Standard payload
    self.send(0x1A, payload)
    # Response: 233B packet with up to 15 action names + metadata
```

### 2️⃣ Enter Teaching Mode (0x0D)
```python
def enter_teaching(self):
    """Enable zero-gravity damping for manual manipulation"""
    payload = bytearray(144)  # 144B = 161B total with header
    # Mode flag at offset 0
    struct.pack_into('>I', payload, 0, 0x00000001)  # Enable damping
    self.send(0x0D, payload)
```

### 3️⃣ Exit Teaching Mode (0x0E)
```python
def exit_teaching(self):
    """Return to normal control"""
    payload = bytearray(44)
    struct.pack_into('>I', payload, 0, 0x00000000)  # Disable damping
    self.send(0x0E, payload)
```

### 4️⃣ Start/Stop Recording (0x0F)
```python
def toggle_recording(self, start=True):
    """Start (True) or stop (False) recording trajectory"""
    payload = bytearray(44)
    flag = 0x00000001 if start else 0x00000000
    struct.pack_into('>I', payload, 0, flag)
    self.send(0x0F, payload)
```

### 5️⃣ Save Teaching Action (0x2B)
```python
def save_action(self, action_name, duration_ms):
    """Save recorded trajectory with name and duration"""
    import time
    payload = bytearray(216)  # 216B = 233B total with header
    
    # Action name (offset 0, 32 bytes)
    name_bytes = action_name.encode('utf-8')[:31]
    payload[0:len(name_bytes)] = name_bytes
    
    # Timestamp (offset 32, 4 bytes)
    struct.pack_into('>I', payload, 32, int(time.time()))
    
    # Duration in ms (offset 36, 4 bytes)
    struct.pack_into('>I', payload, 36, duration_ms)
    
    # Frame count (offset 40, 4 bytes) - auto
    struct.pack_into('>I', payload, 40, 0)
    
    # Flags (offset 44, 4 bytes) - enable save
    struct.pack_into('>I', payload, 44, 0x00000001)
    
    self.send(0x2B, payload)
```

### 6️⃣ Play Teaching Action (0x41)
```python
def play_action(self, action_id):
    """Execute saved teaching action by ID"""
    payload = bytearray(180)  # 180B = 197B total with header
    
    # Action ID (offset 0, 4 bytes) - 1-indexed
    struct.pack_into('>I', payload, 0, action_id)
    
    # Frame count (offset 4, 4 bytes) - 0 = all frames
    struct.pack_into('>I', payload, 4, 0)
    
    # Duration (offset 8, 4 bytes) - 0 = original duration
    struct.pack_into('>I', payload, 8, 0)
    
    # Interpolation mode (offset 12, 4 bytes)
    # 0=Linear, 1=Cubic, 2=Smooth
    struct.pack_into('>I', payload, 12, 1)  # Cubic interpolation
    
    self.send(0x41, payload)
```

---

## 📊 Packet Structure Cheat Sheet

### Header (Same for All Commands)
```
Bytes  0-3:   0x17 0xFE 0xFD 0x00  (Type + Magic)
Bytes  4-5:   0x01 0x00             (Flags)
Bytes  6-7:   [Sequence Number]    (Big-endian uint16)
Bytes  8-9:   0x00 0x00             (Reserved)
Bytes  10-11: 0x00 0x01             (Reserved)
Byte   12:    [Command ID]          (0x0D, 0x0E, 0x0F, 0x1A, 0x2B, 0x41)
Bytes  13-14: [Payload Length]     (Big-endian uint16)
```

### Payload Sizes
```
Standard:        44 bytes (0x2C)
Full State:      144 bytes (0x90)
Trajectory:      180 bytes (0xB4)
Action List:     216 bytes (0xD8)
```

### CRC32 (Last 4 Bytes)
```
Algorithm: IEEE 802.3 polynomial
Byte Order: Big-endian
Range: All bytes from 0 to N-4
```

---

## 🔌 Connection Setup

```python
# Robot discovery (static for now, implement SSDP later)
ROBOT_IP = "192.168.86.3"    # Find via:
                             # - Android app UI
                             # - Router DHCP leases
                             # - ARP scan: arp-scan -I eth0 --localnet
                             # - SSDP multicast (231.1.1.2:10134)

ROBOT_PORT = 49504           # Fixed port (UDP)

# Create packet builder
pkt = TeachModePacket()

# Send initialization sequence (REQUIRED)
pkt.send(0x09, bytearray(44))  # Control mode set
time.sleep(0.1)
pkt.send(0x0A, bytearray(44))  # Parameter sync
time.sleep(0.1)
pkt.send(0x0B, bytearray(44))  # Status subscribe
time.sleep(0.1)
pkt.send(0x0C, bytearray(44))  # Ready signal
time.sleep(1)

# Now teaching mode is enabled
```

---

## ✅ Complete Workflow Example

```python
# 1. List existing actions
pkt.list_actions()
time.sleep(1)

# 2. Enter teaching mode
pkt.enter_teaching()
time.sleep(2)

# 3. Start recording
pkt.toggle_recording(start=True)
time.sleep(10)  # Record for 10 seconds

# 4. Stop recording
pkt.toggle_recording(start=False)
time.sleep(1)

# 5. Save the action
pkt.save_action("my_wave", 10000)  # 10 second action
time.sleep(1)

# 6. Exit teaching mode
pkt.exit_teaching()
time.sleep(1)

# 7. Play back the saved action
pkt.play_action(action_id=1)  # First saved action
time.sleep(15)

# 8. Verify by listing again
pkt.list_actions()
```

---

## 📋 Testing Checklist

- [ ] Robot responds to initialization sequence (0x09-0x0C)
- [ ] Can send 0x1A and receive 233B response with action list
- [ ] Can enter teaching mode (0x0D) with 161B packet
- [ ] Can start/stop recording (0x0F with flag toggle)
- [ ] Can save action (0x2B with name + duration)
- [ ] Can play action (0x41 with action ID)
- [ ] Can exit teaching mode (0x0E)
- [ ] CRC32 checksums validate correctly
- [ ] Sequence numbers increment properly
- [ ] Robot returns error codes on invalid commands

---

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No robot response | Wrong IP/port | Verify 192.168.86.3:49504 |
| CRC mismatch | Calculation error | Use zlib.crc32() |
| Sequence error | Wrong incrementing | Reset to 0 on reconnect |
| Mode not entering | Missing init sequence | Send 0x09-0x0C first |
| Save fails | Invalid action name | Use alphanumeric + underscore |
| Play fails | Invalid action ID | Start at 1, max 15 |

---

## 📚 Full Reference

For complete details including payload structure and evidence, see:
- **[PCAP_ANALYSIS_FINDINGS.md](PCAP_ANALYSIS_FINDINGS.md)** - Full analysis with packet examples
- **[TEACHING_MODE_PROTOCOL_COMPLETE.md](TEACHING_MODE_PROTOCOL_COMPLETE.md)** - Detailed protocol spec

---

**Ready to implement. Start with initialization sequence test.**
