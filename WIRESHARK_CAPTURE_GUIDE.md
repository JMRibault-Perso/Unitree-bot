# Wireshark Protocol Analysis Guide
## Capturing Android App Traffic on Windows

### Step 1: Wireshark Setup

1. **Install Wireshark** (if not already installed)
   - Download from https://www.wireshark.org/download.html
   - Make sure to install with Npcap driver

2. **Identify WiFi Adapter**
   - Open Wireshark
   - Look for your WiFi adapter (e.g., "Wi-Fi", "Wireless Network Connection")
   - Verify it shows your IP on 192.168.86.x network

### Step 2: Start Capture

1. **Set Capture Filter** (optional but recommended)
   - Before starting capture, click "Capture Options"
   - In capture filter field, enter: `host 192.168.86.3`
   - This captures only robot traffic, reducing noise

2. **Start Capture**
   - Double-click your WiFi adapter OR
   - Select adapter and click blue shark fin icon

3. **Verify Capture is Working**
   - Ping robot from Windows: `ping 192.168.86.3`
   - You should see ICMP packets appear in Wireshark

### Step 3: Capture Robot Control

**Important**: Do specific actions so you can correlate them with packets

1. **Baseline Capture** (10 seconds)
   - Robot connected, app open, but no commands
   - This shows "idle" traffic

2. **Single Action Test**
   - Press ONE button in app (e.g., "Wave hand")
   - Note the exact time you pressed it
   - Wait 5 seconds
   - Repeat the SAME action
   - Compare packets at both times to find the command

3. **Command Mapping**
   - Test each major function:
     - Walk forward
     - Walk backward
     - Turn left/right
     - Move arms
     - Stand up/sit down
   - Note timestamp for each action

4. **Status/Video Streams**
   - Let robot run for 30+ seconds
   - Identify continuous streams (battery, sensor data, video)

### Step 4: Stop and Save

1. **Stop Capture** (red square icon)
2. **Save Capture**
   - File → Save As
   - Name: `g1_6937_android_capture_YYYYMMDD.pcapng`
   - Format: pcapng (Wireshark native)

### Step 5: Analysis

#### Find Communication Ports

1. **Statistics → Conversations → TCP/UDP tabs**
   - Shows all unique connections
   - Sort by "Packets" or "Bytes" to find active connections
   - Note: Port numbers used by app and robot

Example output:
```
Address A          Port A    Address B       Port B    Packets
192.168.86.X      54321     192.168.86.3    8080      1234
```

#### Analyze Command Structure

1. **Apply Display Filter**
   - If you found port 8080: `tcp.port == 8080`
   - Or specific stream: `tcp.stream eq 0`

2. **Follow Stream**
   - Right-click a packet → Follow → TCP/UDP Stream
   - Shows entire conversation
   - Look for readable text (JSON, XML) or binary data

3. **Compare Command Packets**
   - Find packet when you pressed "wave" at time T1
   - Find packet when you pressed "wave" at time T2
   - Right-click → Copy → Bytes → Hex Stream
   - Compare hex to find which bytes change/stay same

#### Common Protocol Patterns

**JSON over TCP/WebSocket:**
```
{"command": "move", "direction": "forward", "speed": 0.5}
```

**Binary Protocol:**
```
Header: [0xFF, 0xAA, 0x01]  ← Magic bytes
Length: [0x00, 0x10]        ← Message length
Type:   [0x05]              ← Command type
Data:   [0x12, 0x34, ...]   ← Command parameters
CRC:    [0xAB]              ← Checksum
```

**Protobuf/Custom Binary:**
- Look for repeated byte patterns
- Identify field delimiters
- Note: Little-endian vs big-endian numbers

### Step 6: Document Findings

Create a map of discovered commands:

| Action | Port | Protocol | Hex/Message | Notes |
|--------|------|----------|-------------|-------|
| Walk forward | 8080 | TCP | `{cmd: "move", dir: 1}` | Speed 0-1.0 |
| Wave hand | 8080 | TCP | `{cmd: "arm", gesture: 5}` | gesture ID |

### Step 7: Implement Client

Once you understand the protocol:

**For JSON over HTTP/WebSocket:**
```python
import requests
import json

def walk_forward(speed=0.5):
    cmd = {"command": "move", "direction": "forward", "speed": speed}
    response = requests.post("http://192.168.86.3:8080/control", json=cmd)
    return response.json()
```

**For binary protocol:**
```python
import socket
import struct

def send_command(cmd_type, data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    header = b'\xFF\xAA\x01'
    length = struct.pack('>H', len(data))
    packet = header + length + bytes([cmd_type]) + data
    sock.sendto(packet, ('192.168.86.3', 8080))
    sock.close()
```

### Tips for Success

1. **Capture Multiple Sessions**
   - Compare different capture sessions
   - Verify your understanding is correct

2. **Look for Authentication**
   - App might send auth token at start
   - Check for handshake sequence

3. **Monitor Video Stream**
   - Usually separate port/protocol
   - Might be RTSP, HTTP, or custom UDP

4. **Check for Keep-Alive**
   - Robot might expect periodic heartbeat
   - Note interval and message format

5. **Error Responses**
   - Send invalid commands to see error messages
   - Helps understand protocol validation

### Troubleshooting

**No packets captured:**
- Make sure Android phone is on same WiFi
- Verify robot IP: `ping 192.168.86.3`
- Check capture filter syntax
- Try without capture filter first

**Too many packets:**
- Use display filter: `ip.addr == 192.168.86.3`
- Close other apps using network
- Filter by protocol: `tcp` or `udp`

**Can't see packet content:**
- Might be encrypted (TLS/SSL)
- Check for certificate pinning in app
- May need to root Android and install CA cert

### Next Steps

After analysis, share findings:
1. Port numbers used
2. Protocol type (TCP/UDP, JSON/binary)
3. Sample command hex dumps
4. Authentication method (if any)

This information will help build a PC-based controller!
