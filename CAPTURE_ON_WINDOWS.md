# Capturing Robot Traffic on Windows (with Android App)

## Current Setup
- **WSL2 Linux:** 192.168.86.11 (can't see phone traffic)
- **Android Phone:** Running Unitree app (receives robot data)
- **Robot:** 192.168.86.16 (sends to phone, not PC)

## Problem
The robot sends telemetry/video to **your phone's IP**, not to your PC. WSL2 can't capture traffic between the robot and your phone.

## Solution: Capture on Windows Host

### Method 1: Wireshark on Windows (RECOMMENDED)

1. **Download Wireshark for Windows:** https://www.wireshark.org/download.html

2. **Start Capture:**
   - Open Wireshark
   - Select your WiFi adapter (same network as robot)
   - Click "Start capturing packets"

3. **Apply Display Filter:**
   ```
   ip.addr == 192.168.86.16
   ```

4. **Use the Android App:**
   - Connect to robot
   - Watch video stream
   - Move robot around
   - Wave arm, etc.

5. **Stop and Save:**
   - Stop capture after 1-2 minutes
   - File → Save As → `robot_video_stream.pcapng`
   - Copy to WSL: `\\wsl$\Ubuntu\root\G1\unitree_sdk2\`

6. **Analyze in WSL:**
   ```bash
   cd /root/G1/unitree_sdk2
   ./analyze_capture.sh robot_video_stream.pcapng
   ```

### Method 2: tcpdump on Windows (PowerShell as Admin)

1. **Install npcap:** https://npcap.com/#download

2. **Find your WiFi interface:**
   ```powershell
   Get-NetAdapter | Where-Object {$_.Status -eq "Up"}
   ```

3. **Capture traffic:**
   ```powershell
   # Install Wireshark command-line tools or use tshark
   tshark -i "Wi-Fi" -f "host 192.168.86.16" -w robot_capture.pcap
   # Press Ctrl+C after 1-2 minutes
   ```

4. **Copy to WSL:**
   ```powershell
   Copy-Item robot_capture.pcap \\wsl$\Ubuntu\root\G1\unitree_sdk2\
   ```

### Method 3: Network Tap (Advanced)

Use your PC as a transparent bridge:

1. **Enable IP Forwarding in Windows**
2. **Create WiFi hotspot** - have phone connect through PC
3. **Capture forwarded traffic** - see all robot↔phone packets

## What to Look For in Capture

### Video Stream
- **Protocol:** Likely RTP/RTSP over UDP or WebRTC
- **Ports:** Dynamic, look for large packets (1000+ bytes)
- **Codec:** H.264 or H.265 (check for SPS/PPS NAL units)

### Telemetry
- **Ports:** 47707, 33280, 51042 (from previous analysis)
- **Size:** 88 bytes per packet
- **Frequency:** ~20 Hz (every 50ms)

### Commands (if sent locally)
- **Look for:** Packets FROM phone TO robot (192.168.86.16)
- **Protocol:** Could be UDP, TCP, or WebSocket
- **Timing:** Correlate with button presses in app

## Analysis Commands (After Copying to WSL)

```bash
cd /root/G1/unitree_sdk2

# Quick overview
./analyze_capture.sh robot_video_stream.pcapng

# Find video stream
tcpdump -r robot_video_stream.pcapng -n 'src 192.168.86.16 and udp' \
  | awk '{print $5, $NF}' | sort | uniq -c | sort -rn | head -20

# Extract video packets (assuming port 5000)
tcpdump -r robot_video_stream.pcapng -n 'port 5000' -w video_only.pcap

# Look for H.264 NAL units
tcpdump -r video_only.pcap -X | grep -A 5 "0000 0001"

# Find phone's IP
tcpdump -r robot_video_stream.pcapng -n 'dst 192.168.86.16' \
  | awk '{print $3}' | cut -d. -f1-4 | sort -u

# Check for command packets
tcpdump -r robot_video_stream.pcapng -n \
  'dst 192.168.86.16 and not (port 53 or port 5353)'
```

## Alternative: Monitor Mode WiFi Capture

If your Windows WiFi adapter supports monitor mode:

1. **Use Acrylic Wi-Fi Home:** https://www.acrylicwifi.com/
2. **Or Wireshark + Npcap in monitor mode**
3. **Capture all WiFi packets** - no need to be on network
4. **Filter for robot MAC address**

## Expected Results

After capturing with Android app connected:

- ✅ **Discovery:** Robot broadcasts to 231.1.1.2:10134 (JSON)
- ✅ **Telemetry:** Robot → Phone (88-byte packets, 20 Hz)
- ✅ **Video:** Robot → Phone (large UDP packets, continuous)
- ❓ **Commands:** Phone → Robot (this is what we need to find!)
- ❌ **Cloud:** Phone → global-robot-api.unitree.com (if commands go to cloud)

## Next Steps After Capture

1. **Identify phone IP** - which device received the video?
2. **Find video port** - what port is streaming?
3. **Extract video codec** - can we decode it?
4. **Find command channel** - does phone send UDP/TCP to robot?
5. **Reverse protocol** - if local commands exist, what's the format?

If you find **no packets from phone to robot**, then:
- All commands go through cloud (global-robot-api.unitree.com)
- Local control requires cloud registration
- Need to enable cloud mode or find alternative SDK method
