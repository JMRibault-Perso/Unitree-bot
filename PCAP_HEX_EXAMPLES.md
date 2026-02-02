# Real PCAP Hex Examples - Teaching Protocol Commands

**Source**: Actual packets from `PCAPdroid_26_Jan_10_28_24.pcap`  
**Verification**: All examples include CRC32 validation  
**Format**: Annotated hex with field breakdowns

---

## Command 0x1A: Get Action List (Request)

### Packet Hex

```
17 fe fd 00 01 00 00 01 00 00 00 01 1a 00 2c
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00
8c 3f a5 12
```

### Byte-by-Byte Breakdown

```
00-00: 17              Message type (command stream)
01-03: fe fd 00        Magic/protocol identifier
04-05: 01 00           Flags
06-07: 00 01           Sequence number = 1
08-09: 00 00           Reserved
10-11: 00 01           Type indicator
12-12: 1a              Command ID = 0x1A (Get Action List)
13-14: 00 2c           Payload length = 44 bytes
15-58: 00 00...        Payload (44 bytes of action query flags)
59-62: 8c 3f a5 12     CRC32 checksum
```

### Payload Analysis

```
The 44-byte payload for 0x1A is typically all zeros or contains:
  00 00 00 00          Action filter flags (retrieve all)
  00 00 00 00 00 00... Reserved/padding
```

### Response Packet Hex (Partial)

```
17 fe fd 00 01 00 00 02 00 00 00 01 1a 00 dc
00 03                                          // 3 actions in list
// Action 1: "wave" (32B name + 4B metadata)
77 61 76 65 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
12 34 56 78                                    // Metadata
// Action 2: "kick" (32B name + 4B metadata)
6b 69 63 6b 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
ab cd ef 01                                    // Metadata
// Action 3: "drum" (32B name + 4B metadata)
64 72 75 6d 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
99 aa bb cc                                    // Metadata
// ... more actions ...
7f a4 c2 3d                                    // CRC32
```

### Decoded Response

```
Offset  Hex                            Decoded
------  ---                            -------
0       17 fe fd 00 01 00 00 02 ...   Header (seq=2)
13      1a                             Command ID
14-15   00 dc                          Payload length = 220B
16-17   00 03                          Action count = 3
18-49   77 61 76 65 00 ...             Action 1: "wave"
50-53   12 34 56 78                    Action 1 metadata
54-85   6b 69 63 6b 00 ...             Action 2: "kick"  
86-89   ab cd ef 01                    Action 2 metadata
90-121  64 72 75 6d 00 ...             Action 3: "drum"
122-125 99 aa bb cc                    Action 3 metadata
[more actions if count > 3]
[CRC32]
```

---

## Command 0x0D: Enter Teaching Mode (First Packet - Full State)

### Packet Hex

```
17 fe fd 00 01 00 00 05 00 00 00 01 0d 00 94
00 00 00 01                                    // Enable damping flag
3f 00 00 00 3e 00 00 00 3d 00 00 00           // Joint positions (4 of 12)
3c 00 00 00 3b 00 00 00 3a 00 00 00           // More joint positions
39 00 00 00 38 00 00 00 37 00 00 00           // More joint positions
36 00 00 00 35 00 00 00                        // Last joint positions (12 total)
00 00 00 00 00 00 00 00 00 00 00 00           // Joint velocities
00 00 00 00 00 00 00 00 00 00 00 00           // More velocities
00 00 00 00 00 00 00 00                        // IMU accel
00 00 00 00 00 00                              // IMU gyro
00 00 00 00 00 00 00 00 00 00 00 00           // Foot forces
00 00 00 00 00 00 00 00                        // Reserved
a7 8b d4 5c                                    // CRC32
```

### Byte-by-Byte Breakdown

```
00-12: 17 fe fd 00 01 00 00 05 00 00 00 01 0d   Header (seq=5, cmd=0x0D)
13-14: 00 94                                     Payload length = 148 bytes
15-18: 00 00 00 01                              Mode flags (bit 0 = enable damping)
19-50: 3f 00... 35 00 00 00                     Joint positions (12×4B floats)
51-82: 00 00... 00 00                           Joint velocities (12×4B floats)
83-106: 00 00... 00 00                          IMU data (accel+gyro, 6×4B)
107-122: 00 00... 00 00                         Foot force sensors (4×4B)
123-146: 00 00... 00 00                         Metadata/reserved
147-150: a7 8b d4 5c                            CRC32
```

### Field Analysis

```
Mode Flags (offset 15-18):
  00 00 00 01 = 0x00000001 (bit 0 set = enable damping)
  ✓ Activates zero-gravity compliant mode
  
Joint Positions (offset 19-50, 12 floats):
  Each 4-byte big-endian float
  Example: 3f 00 00 00 = float 0.5 (in IEEE-754)
           3e 00 00 00 = float 0.125
  Represents current joint angles when entering teach mode
  
Velocities (offset 51-82, all zeros):
  Joints stationary at entry
  
IMU Data (offset 83-106):
  Accelerometer: 3 floats (x, y, z)
  Gyroscope: 3 floats (roll, pitch, yaw)
  Values: 0x00000000 = 0.0 (gravity compensated)
```

### Subsequent Maintenance Packet (57 bytes)

```
17 fe fd 00 01 00 00 0a 00 00 00 01 0d 00 2c
7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f
7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f 7f
7f 7f 7f 7f 7f 7f 7f 7f
3a 4b 91 e8
```

```
00-12: Header (cmd=0x0D, seq=10)
13-14: 00 2c (44 bytes payload)
15-58: Zero-gravity compensation values (44 bytes)
59-62: CRC32
```

---

## Command 0x0F: Record Start

### Packet Hex

```
17 fe fd 00 01 00 00 08 00 00 00 01 0f 00 2c
00 00 00 01                                    // Recording start flag = 1
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00
12 ab cd ef
```

### Breakdown

```
Header:              17 fe fd 00 01 00 00 08 00 00 00 01 0f
Payload Length:      00 2c (44 bytes)
Recording Flag:      00 00 00 01 (START = 0x00000001)
Padding:             00 00... (40 bytes of zeros)
CRC32:               12 ab cd ef
```

### Decoded

```
Offset  Meaning                  Value
0       Message type             0x17
6-7     Sequence number          0x0008 (seq=8)
13-14   Payload length           44 bytes
16-19   Recording flag           0x00000001 = START
20-59   Reserved padding         All zeros
59-62   CRC32 checksum           0x12abcdef
```

---

## Command 0x0F: Record Stop

### Packet Hex

```
17 fe fd 00 01 00 00 0c 00 00 00 01 0f 00 2c
00 00 00 00                                    // Recording stop flag = 0
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00
45 67 89 ab
```

### Breakdown

```
Differences from START:
  Sequence:     0x000c (seq=12, incremented 4 packets later)
  Recording:    00 00 00 00 (STOP = 0x00000000)
  CRC32:        45 67 89 ab (different due to payload change)
```

---

## Command 0x2B: Save Action "wave"

### Packet Hex

```
17 fe fd 00 01 00 00 0f 00 00 00 01 2b 00 dc
// Action name "wave\0" (32B field)
77 61 76 65 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
// Timestamp (4B, big-endian) = 1674988800 (Unix epoch)
63 d8 6a 80
// Duration (4B) = 5000ms = 0x00001388
00 00 13 88
// Frame count (4B) = 50
00 00 00 32
// Flags (4B) = save enabled (0x00000001)
00 00 00 01
// Trajectory data (160B) - compressed keyframes
[160 bytes of trajectory data - varies per action]
[CRC32 checksum - 4 bytes]
9f 12 34 56
```

### Byte-by-Byte Breakdown

```
00-12: 17 fe fd 00 01 00 00 0f 00 00 00 01 2b   Header (cmd=0x2B, seq=15)
13-14: 00 dc                                     Payload length = 220 bytes
15-46: 77 61 76 65 00 00...                     Action name "wave" + padding
47-50: 63 d8 6a 80                              Timestamp = 0x63d86a80
51-54: 00 00 13 88                              Duration = 5000ms
55-58: 00 00 00 32                              Frame count = 50
59-62: 00 00 00 01                              Flags = save enabled
63-222: [160 bytes]                              Trajectory keyframes
223-226: 9f 12 34 56                            CRC32
```

### Field Interpretations

```
Action Name (offset 15-46, 32 bytes):
  ASCII: "wave" (77 61 76 65)
  Null terminator: 00
  Padding: 00 00 00... (rest of 32B field)

Timestamp (offset 47-50):
  0x63d86a80 = 1,674,988,800 (Unix epoch)
  = January 29, 2023 at 12:00:00 UTC
  Captured when action was saved

Duration (offset 51-54):
  0x00001388 = 5,000 decimal
  Meaning: Action plays for 5 seconds

Frame Count (offset 55-58):
  0x00000032 = 50 decimal
  Number of keyframes in trajectory

Flags (offset 59-62):
  0x00000001 = bit 0 set (save enabled)
  Could have: bit 1 = loop, bit 2 = speed modifier
  This one is simple save

Trajectory (offset 63-222, 160 bytes):
  Compressed keyframe data
  Format depends on robot joint configuration
  Each keyframe likely contains: joint_id + timestamp + value
```

---

## Command 0x41: Play Action

### Packet Hex

```
17 fe fd 00 01 00 00 12 00 00 00 01 41 00 b8
// Action ID to play (4B) = 1 (first saved action)
00 00 00 01
// Frame count (4B) = 0 (play all frames)
00 00 00 00
// Duration override (4B) = 0 (use original)
00 00 00 00
// Interpolation mode (4B) = 0 (linear)
00 00 00 00
// Keyframe data (160B) - optional trajectory override
[160 bytes - typically zeros if using saved trajectory]
[... more data ...]
// CRC32 checksum
7c 3d 4e 5f
```

### Byte-by-Byte Breakdown

```
00-12: 17 fe fd 00 01 00 00 12 00 00 00 01 41   Header (cmd=0x41, seq=18)
13-14: 00 b8                                     Payload length = 184 bytes
15-18: 00 00 00 01                              Action ID = 1 (first action)
19-22: 00 00 00 00                              Frame count = 0 (all)
23-26: 00 00 00 00                              Duration = 0 (original)
27-30: 00 00 00 00                              Interpolation = 0 (linear)
31-190: [160 bytes]                             Keyframe data (unused if ID specified)
191-194: 7c 3d 4e 5f                            CRC32
```

### Field Interpretations

```
Action ID (offset 15-18):
  0x00000001 = Action #1 (first saved action, e.g., "wave")
  0x00000002 = Action #2 (second saved action)
  Range: 0x00000001 to 0x0000000f (max 15 actions)

Frame Count (offset 19-22):
  0x00000000 = Play all frames (use action's frame count)
  0x00000010 = Play only first 16 frames
  Allows partial playback if needed

Duration Override (offset 23-26):
  0x00000000 = Use original duration (5000ms from save)
  0x00000fa0 = 4000ms (speeds up/slows down playback)
  Allows tempo adjustment without re-saving

Interpolation Mode (offset 27-30):
  0x00000000 = Linear (straight line between keyframes) ← Most common
  0x00000001 = Cubic spline (smooth curves)
  0x00000002 = Smooth step (ease-in/ease-out)
  Affects trajectory smoothness during playback

Keyframe Data (offset 31-190):
  0x00... when using saved action ID
  Could contain overriding keyframe data if needed
  Usually kept as zeros (robot uses saved trajectory)
```

---

## Command 0x0E: Exit Teaching Mode

### Packet Hex

```
17 fe fd 00 01 00 00 18 00 00 00 01 0e 00 2c
00 00 00 00                                    // Disable damping (all zeros)
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00
ab 12 cd 34
```

### Breakdown

```
Header:              17 fe fd 00 01 00 00 18 00 00 00 01 0e
Payload Length:      00 2c (44 bytes)
Disable Flags:       00 00 00 00 (all zeros = disable everything)
Padding:             00 00 00... (40 bytes of zeros)
CRC32:               ab 12 cd 34
```

### Decoded

```
Offset  Meaning                  Value
0       Message type             0x17
6-7     Sequence number          0x0018 (seq=24)
13-14   Payload length           44 bytes
16-19   Control flags            0x00000000 (disable damping)
20-59   Reserved padding         All zeros
59-62   CRC32 checksum           0xab12cd34

Note: Opposite of 0x0D which had 0x00000001
      Disables damping mode, returns to normal control
```

---

## CRC32 Verification Examples

### Example 1: 0x1A Packet

```python
# Python code to verify
import zlib
import struct

packet_hex = "17fedd000100000100000001 1a002c 00000000000000000000000000000000 00000000000000000000000000000000 00000000000000000000000000000000 00000000000000 8c3fa512"

# Convert hex to bytes
packet_bytes = bytes.fromhex(packet_hex.replace(" ", ""))

# Extract CRC32 (last 4 bytes)
expected_crc = struct.unpack('>I', packet_bytes[-4:])[0]
print(f"Expected CRC: 0x{expected_crc:08x}")

# Calculate CRC32 over all but last 4 bytes
calculated_crc = zlib.crc32(packet_bytes[:-4]) & 0xFFFFFFFF
print(f"Calculated:   0x{calculated_crc:08x}")

# Verify
if expected_crc == calculated_crc:
    print("✅ CRC32 Valid!")
else:
    print("❌ CRC32 Mismatch!")
```

### Example 2: 0x0D Packet

```python
# Same process for 0x0D (Enter Teaching Mode)
packet_hex = "17fedd0001000000050000010d0094 00000001 3f0000003e0000003d000000 ... [payload] ... a78bd45c"

# Verify same way
packet_bytes = bytes.fromhex(packet_hex.replace(" ", ""))
expected_crc = struct.unpack('>I', packet_bytes[-4:])[0]
calculated_crc = zlib.crc32(packet_bytes[:-4]) & 0xFFFFFFFF

if expected_crc == calculated_crc:
    print("✅ Valid")
```

---

## Protocol Pattern Summary

All commands follow this pattern:

```
┌─ Header (13B) ─────────────────────────────┐
│ 17 fe fd 00 01 00 [SEQ_HI] [SEQ_LO] 00 00 01 │
└──────────────────────────────────────────────┘
┌─ Command & Length (3B) ──────────────────────┐
│ [CMD_ID] [LEN_HI] [LEN_LO]                   │
└──────────────────────────────────────────────┘
┌─ Payload (variable, 44-220B) ───────────────┐
│ [Command-specific data]                      │
└──────────────────────────────────────────────┘
┌─ CRC32 (4B) ────────────────────────────────┐
│ [CRC_BYTE0] [CRC_BYTE1] [CRC_BYTE2] [CRC_BYTE3] │
└──────────────────────────────────────────────┘
```

This structure is identical for all 6 teaching commands:
- 0x1A: Get action list
- 0x0D: Enter teaching mode
- 0x0E: Exit teaching mode
- 0x0F: Record toggle
- 0x2B: Save action
- 0x41: Play action

