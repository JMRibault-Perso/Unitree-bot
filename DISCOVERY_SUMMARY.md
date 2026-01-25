# Unitree G1 Discovery Protocol - Reverse Engineered

## Robot Information
- **Serial Number:** E21D1000PAHBMB06
- **Device Name:** unitree_dapengche (G1_6937 in cloud)
- **Current IP:** 192.168.86.16
- **mDNS Hostname:** Unitree.local

## Discovery Protocol

### 1. Multicast Discovery Broadcast
**Destination:** 231.1.1.2:10134 (UDP)  
**Frequency:** On boot and WiFi connection  
**Payload Format:** JSON

```json
{
  "sn": "E21D1000PAHBMB06",
  "key": "",
  "name": "unitree_dapengche",
  "ip": "192.168.86.16"
}
```

**How Android App Discovers Robot:**
- Listens on multicast group 231.1.1.2:10134
- Receives robot's JSON announcement
- Extracts robot IP and serial number
- No authentication needed for discovery

### 2. mDNS Announcement
**Service:** Unitree.local (mDNS port 5353)  
**Records Advertised:**
- PTR: Unitree.local
- A: 192.168.86.16
- AAAA: fe80::6bb3:c21d:481f:275c (IPv6 link-local)

**How to Query:**
```bash
# DNS-SD query
avahi-browse -r _unitree._tcp
# or
dns-sd -B _unitree._tcp
```

### 3. Telemetry Stream (UNCONFIRMED - needs Android app running)
**Source Port:** Robot sends from dynamic port (e.g., 53931)  
**Destination Ports:** 47707, 33280, 51042 (on phone)  
**Packet Size:** 88 bytes  
**Frequency:** ~20 Hz (every 50ms)  
**Protocol:** Binary (likely WebRTC/STUN or custom)

**Pattern from PCAP:**
```
Offset  Hex Data
0x0000: 01 00 00 44  (Possible message type/length)
0x0004: 21 12 a4 42  (STUN magic cookie candidate)
0x0008: ... (encrypted or binary state data)
```

### 4. Cloud Connection
**Robot queries:** gpt-proxy.unitree.com (8.222.78.102)  
**Purpose:** Cloud services, GPT integration  
**Protocol:** ICMP ping + likely HTTPS

**Phone queries:** global-robot-api.unitree.com  
**Purpose:** WebRTC signaling, command routing  
**Status:** Robot NOT registered (all cloud control attempts fail)

## Android App Communication Flow

### Discovery Phase
1. App starts and joins multicast group 231.1.1.2
2. Waits for robot discovery broadcast
3. Receives robot JSON with IP/serial
4. Optionally queries Unitree.local via mDNS

### Telemetry Phase (Local)
1. App opens UDP sockets on ports 47707, 33280, 51042
2. Robot detects phone IP (from network traffic or multicast response)
3. Robot streams 88-byte telemetry packets to phone
4. **ONE-WAY COMMUNICATION** (robot → phone only)

### Control Phase (Cloud)
1. App sends commands via HTTPS to global-robot-api.unitree.com
2. Cloud relays commands to robot
3. **Robot must be online and registered for this to work**
4. **G1_6937 is NOT cloud-registered** → all cloud commands fail

## Key Findings

### ✅ What Works Locally
- Robot discovery via multicast (231.1.1.2:10134)
- Robot mDNS announcement (Unitree.local)
- Robot → Phone telemetry stream (UDP ports 47707/33280/51042)
- Robot pings gpt-proxy.unitree.com

### ❌ What Requires Cloud
- Command/control (no local UDP packets phone → robot)
- Arm movements, walking, mode switching
- Video streaming (not found in local traffic)
- Audio TTS/ASR

### 🤔 Unknowns
- How to trigger robot to send telemetry (does it auto-detect phone?)
- How to decode 88-byte telemetry packets
- Is there a hidden local control protocol?
- Why does SDK WebRTC fail? (ports 8081, 9991 closed)

## Testing Setup

### Listener Scripts Created

**1. Discovery Listener** (`discover_robot.py`)
```bash
python3 discover_robot.py
# Listens on 231.1.1.2:10134 for robot announcements
# Power-cycle robot to trigger broadcast
```

**2. Telemetry Listener** (`listen_telemetry.py`)
```bash
python3 listen_telemetry.py
# Listens on ports 47707, 33280, 51042
# Open Android app to trigger telemetry stream
```

### Live Capture Commands
```bash
# Capture discovery
sudo tcpdump -i eth1 -n 'dst 231.1.1.2 and port 10134' -X

# Capture telemetry
sudo tcpdump -i eth1 -n 'host 192.168.86.16 and udp' -X

# Full capture with Android app
sudo tcpdump -i eth1 -n 'host 192.168.86.16' -w robot_app_session.pcap
```

## Next Steps

### To Control Robot Locally (Hypothesis)
1. **Trigger telemetry stream** - Open Android app, capture traffic
2. **Reverse-engineer 88-byte telemetry** - Identify state fields
3. **Look for response channel** - Check if sending UDP to robot works
4. **Test direct port access** - Try ports seen in SDK (8081, 9991)
5. **Sniff app startup** - Capture full app initialization sequence

### Alternative: Enable Cloud Mode
1. Contact Unitree support to enable cloud registration
2. May require firmware update or special configuration
3. Would enable WebRTC control via unitree_webrtc_connect

### Alternative: Enable SDK/DDS Mode
1. Check if G1 Air supports SDK (may need hardware upgrade to EDU)
2. Look for "Developer Mode" in robot settings
3. Try connecting via R3-1 remote to enable SDK mode

## Captured Files
- `full boot.pcapng` - Robot boot sequence (192.168.137.164 in hotspot mode)
- `AP to STA-L.pcapng` - Robot joining WiFi (192.168.86.16)
- `g1-android.pcapng` - Android app session (partial)

## References
- Multicast group 231.1.1.2 is non-standard (not IANA reserved)
- Ports 47707, 33280, 51042 are ephemeral/dynamic
- STUN magic cookie: 0x2112A442 (RFC 5389) - possible WebRTC
