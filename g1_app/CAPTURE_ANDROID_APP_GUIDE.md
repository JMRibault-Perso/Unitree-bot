# Guide: Capturing Android App Traffic to Discover Teaching Mode APIs

## Problem
The teaching mode.pcapng file was captured but doesn't contain any IP traffic between the phone (192.168.137.220) and robot (192.168.137.164). This was likely captured on the wrong interface or only captured local loopback traffic.

## Network Setup Detected
- **Phone**: 192.168.137.220
- **Robot**: 192.168.137.164
- **Network**: 192.168.137.0/24 (hotspot or local WiFi)
- **This analysis machine**: 192.168.86.10/22 (different network, cannot access)

## Methods to Capture App Traffic

### Method 1: Capture on PC with WiFi Adapter (RECOMMENDED)

If you have a PC with WiFi that can join the 192.168.137.x network:

```bash
# 1. Join the same WiFi network as phone and robot
# 2. Install Wireshark
sudo apt-get install wireshark tshark

# 3. Find the correct interface
ip addr show  # Look for 192.168.137.x address

# 4. Start capture (replace wlan0 with your WiFi interface)
sudo wireshark &
# OR command line:
sudo tshark -i wlan0 -f "host 192.168.137.220 or host 192.168.137.164" -w teaching_mode_complete.pcap

# 5. Use Unitree app on phone:
#    - Enter teach mode
#    - Start recording
#    - Move arms
#    - Stop recording  
#    - Save action with name
#    - Play back action
#    - Get action list
# 6. Stop capture
```

### Method 2: Android ADB + tcpdump

If you have USB debugging enabled on the phone:

```bash
# 1. Enable Developer Options on Android:
#    Settings → About Phone → Tap "Build Number" 7 times
#    Settings → Developer Options → Enable USB Debugging

# 2. Connect phone to PC via USB
adb devices  # Should show your device

# 3. Install tcpdump on Android
adb push /path/to/tcpdump /data/local/tmp/
adb shell chmod 755 /data/local/tmp/tcpdump

# 4. Start capture on phone
adb shell "su -c '/data/local/tmp/tcpdump -i wlan0 -s 0 -w /sdcard/robot_traffic.pcap host 192.168.137.164'"

# 5. Use Unitree app (teaching mode sequence)

# 6. Stop capture (Ctrl+C)

# 7. Pull pcap file
adb pull /sdcard/robot_traffic.pcap ./
```

### Method 3: mitmproxy (For HTTPS Inspection)

If the app uses HTTPS (likely):

```bash
# 1. Install mitmproxy
pip install mitmproxy

# 2. Start mitmproxy on PC
mitmproxy --mode transparent --showhost

# 3. Configure Android to use PC as proxy:
#    Settings → WiFi → Long press network → Modify
#    Proxy: Manual
#    Hostname: <PC_IP>
#    Port: 8080

# 4. Install mitmproxy CA certificate on Android:
#    Open browser to http://mitm.it
#    Download Android certificate
#    Install in Settings → Security → Install from storage

# 5. Use Unitree app (if it respects system proxy)
```

### Method 4: Router Port Mirroring

If you control the WiFi router:

```bash
# Configure router to mirror all traffic from 192.168.137.220 to capture PC
# (Router-specific, check your router's admin panel)

# Then capture on PC:
sudo tcpdump -i eth0 -w robot_capture.pcap 'host 192.168.137.220 or host 192.168.137.164'
```

## What to Look For in Capture

### WebRTC Datachannel
The app likely uses WebRTC datachannel for robot control:

**Wireshark Filter:**
```
(ip.addr == 192.168.137.164) && (udp || tcp.port == 8080)
```

**Look for:**
- STUN packets (UDP port 3478 or 19302)
- DTLS handshakes (encrypted UDP)
- SCTP over DTLS (datachannel protocol)
- Signaling traffic (WebSocket or HTTP to turn/stun server)

### HTTP/WebSocket
If the app uses HTTP REST API or WebSocket:

**Wireshark Filter:**
```
(ip.addr == 192.168.137.164) && (http || websocket)
```

**Look for JSON payloads:**
```json
{
  "api_id": 7109,
  "parameter": {...}
}
```

## Analyzing the Capture

### In Wireshark:

1. **Follow TCP Stream**: Right-click packet → Follow → TCP Stream
2. **Follow UDP Stream**: For WebRTC datachannel (if not encrypted)
3. **Export Objects**: File → Export Objects → HTTP to save JSON files
4. **Decrypt DTLS**: If you have the private key (unlikely)

### Using tshark:

```bash
# Extract HTTP requests
tshark -r teaching_mode.pcap -Y "http.request" -T fields -e http.request.method -e http.request.uri -e http.request.full_uri

# Extract JSON from HTTP
tshark -r teaching_mode.pcap -Y "http && json" -T json > http_json.json

# Show WebSocket data
tshark -r teaching_mode.pcap -Y "websocket" -T fields -e websocket.payload
```

### Using Python + scapy:

```python
from scapy.all import rdpcap, TCP, Raw
import json

pcap = rdpcap("teaching_mode_complete.pcap")

for pkt in pcap:
    if TCP in pkt and Raw in pkt:
        payload = bytes(pkt[Raw])
        # Try to decode as JSON
        try:
            if b'{' in payload:
                json_start = payload.index(b'{')
                json_end = payload.rindex(b'}') + 1
                json_data = json.loads(payload[json_start:json_end])
                if 'api_id' in json_data:
                    print(f"API Call: {json_data}")
        except:
            pass
```

## Expected API Calls During Teaching Sequence

Based on our hypothesis, during a teach mode session you should see:

### 1. Enter Teach Mode
```json
{"api_id": 7102, "parameter": {"mode": 0}}  // SetBalanceMode(0) → FSM 501
{"api_id": 7106, "parameter": {"action_id": 99}}  // RELEASE_ARM
```

### 2. Start Recording (HYPOTHETICAL API 7109)
```json
{"api_id": 7109, "parameter": {}}  // or {"action_name": "..."}?
```

### 3. Stop Recording (HYPOTHETICAL API 7110)
```json
{"api_id": 7110, "parameter": {}}
```

### 4. Save Recording (HYPOTHETICAL API 7111)
```json
{"api_id": 7111, "parameter": {"action_name": "wave_hello"}}
```

### 5. Get Action List
```json
{"api_id": 7107, "parameter": {}}
```

### 6. Playback Saved Action
```json
{"api_id": 7108, "parameter": {"action_name": "wave_hello"}}
```

### 7. Delete Action (HYPOTHETICAL API 7112)
```json
{"api_id": 7112, "parameter": {"action_name": "wave_hello"}}
```

## Alternative: Reverse Engineer the APK

If packet capture fails (encrypted WebRTC):

```bash
# 1. Extract APK from phone
adb shell pm list packages | grep unitree
adb shell pm path com.unitree.explore  # Get APK path
adb pull /data/app/~~randomhash~~/com.unitree.explore/base.apk

# 2. Decompile with jadx
git clone https://github.com/skylot/jadx
cd jadx && ./gradlew dist
./build/jadx/bin/jadx-gui base.apk

# 3. Search for:
#    - "7109", "7110", "7111", "7112" (API IDs)
#    - "record", "teach", "save_action"
#    - Classes related to arm control
#    - WebRTC datachannel message formatting
```

## Quick Test on Real Robot

Instead of capturing, test the experimental APIs directly:

```bash
# 1. Make sure robot and PC are on same network
# 2. Update robot IP in g1_app/core/robot_connection.py
# 3. Restart web server
pkill -f web_server.py
cd /root/G1/unitree_sdk2/g1_app/ui
python3 web_server.py &

# 4. Open web UI, enter teach mode
# 5. Try experimental recording APIs:
curl -X POST http://localhost:8000/api/teach/start_recording
# Manually move arms
curl -X POST http://localhost:8000/api/teach/stop_recording
curl -X POST "http://localhost:8000/api/teach/save_recording?action_name=test1"

# 6. Check logs for responses
tail -f /tmp/web_server.log
```

## Summary

**You need to recapture the pcap on a machine that:**
1. Is on the 192.168.137.x network (same as phone and robot)
2. Captures on the correct WiFi interface
3. Runs during the complete teach mode sequence

**Or use the experimental API approach:**
- Test APIs 7109-7112 directly on robot via web controller
- Check robot's response to determine if they exist
- Document actual request/response format if they work
