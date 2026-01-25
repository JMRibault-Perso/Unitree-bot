# Robot Boot Sequence Analysis

## Discovered Robot Broadcasts

I found the robot broadcast messages during boot sequence! Here are the key findings:

### Robot Discovery Protocol

1. **Robot received broadcast from another device (192.168.137.220):**
   ```
   18:46:57.499460 IP 192.168.137.220.37555 > 231.1.1.2.10131: UDP, length 61
   JSON: {"sn":"E21D1000PAHBMB06","key":"","name":"unitree_dapengche"}
   ```

2. **Robot responds with its own broadcast:**
   ```
   18:46:58.140410 IP 192.168.137.164.40608 > 231.1.1.2.10134: UDP, length 91
   JSON: {"sn": "E21D1000PAHBMB06", "key": "", "name": "unitree_dapengche", "ip": "192.168.137.164"}
   ```

### Key Findings

1. **Robot Serial Number**: E21D1000PAHBMB06 (matches our stored data)
2. **Robot Name**: unitree_dapengche (NOT "G1_6937" as expected!)
3. **Discovery Protocol**: UDP multicast to 231.1.1.2
   - Port 10131 for queries
   - Port 10134 for robot responses
4. **IP Address**: Robot correctly announces its current IP (192.168.137.164)

### Network Communication Pattern

The robot also sends encrypted UDP streams to another device at 192.168.86.9 on multiple ports (47707, 33280, 51042). This appears to be the mobile phone/app communication channel, possibly for video streaming or control data.

### Critical Discovery

**The robot name is "unitree_dapengche", NOT "G1_6937"!**

This explains why we haven't found the "G1_6937" identifier - the user expected name doesn't match the actual robot broadcast name. The robot announces itself as "unitree_dapengche" in all discovery messages.

### Protocol Implementation

For our robot discovery system to work correctly, we need to:
1. Listen for UDP broadcasts on multicast 231.1.1.2:10134
2. Parse JSON messages containing: `{"sn": "...", "key": "", "name": "...", "ip": "..."}`
3. Store robot by serial number (E21D1000PAHBMB06) and name (unitree_dapengche)
4. Update IP addresses dynamically as robot announces them

The robot discovery system we built should work correctly with these findings!