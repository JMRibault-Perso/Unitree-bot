# Robot Discovery Explained

## The Problem

You want the system to discover "G1_6937" by name (like the Android app shows), WITHOUT using IP addresses.

## The Reality for G1 Air

**G1 Air models do NOT support automatic discovery.** Here's why:

### What the Android App Actually Does

1. **Initial Binding**: The Android app pairs with the robot via Bluetooth or direct WiFi AP connection
2. **Stores Robot Info**: Saves the robot name (G1_6937) and serial number locally on the phone
3. **Network Connection**: When on the same WiFi, it finds the robot using:
   - **Stored IP** from previous connection, OR
   - **mDNS broadcast** (if robot has Jetson NX), OR
   - **Manual reconnection** through robot's AP mode

### What G1 Air Cannot Do

- ❌ **NO DDS broadcast** without Jetson Orin NX
- ❌ **NO mDNS discovery** - robot doesn't advertise its name on the network
- ❌ **NO multicast/broadcast packets** for discovery
- ❌ **NO SDK mode** that enables discovery protocols

### What We Tested

```bash
# mDNS discovery - FAILED (no broadcasts)
zeroconf listening on _unitree._tcp.local → No robots found

# DDS discovery - FAILED (requires Jetson NX)  
ddsls -a → Robot doesn't publish DDS participants

# Multicast discovery - FAILED (no response)
Listening on 231.1.1.2:10134 → No discovery packets

# Network scan - WORKS but violates "no IP" requirement
ping 192.168.86.2 → Success (but this IS using IP!)
```

## The Only Solutions

### Option 1: Use IP (Current Implementation)
```python
# Bind robot WITH IP after you connect once
POST /api/bind {"name":"G1_6937", "serial":"E21D1000PAHBMB06", "ip":"192.168.86.2"}
# System saves IP and monitors it
```

✅ **This works** but requires knowing the IP  
❌ Violates your "no IP" requirement

### Option 2: Upgrade to G1 EDU
- G1 EDU has Jetson Orin NX
- Supports full SDK/DDS
- Would broadcast discovery packets
- More expensive

### Option 3: Reverse-Engineer Android App Protocol
The Android app likely uses a **proprietary Unitree protocol**, not standard mDNS/DDS.

Steps to discover it:
```bash
# Capture Android app traffic on Windows
1. Open Wireshark
2. Filter: host 192.168.86.2  
3. Use Android app
4. Analyze packets for discovery protocol

# Look for:
- UDP broadcasts on specific ports
- Custom protocol headers
- Discovery request/response patterns
```

If we find the protocol, we can implement it.

## Current System State

**Your robot binding:**
```json
{
  "name": "G1_6937",
  "serial_number": "E21D1000PAHBMB06",
  "ip": null,
  "is_bound": true,
  "is_online": false
}
```

**What this means:**
- ✅ Robot is bound by NAME (not IP)
- ❌ System cannot discover IP automatically (G1 Air limitation)
- ❌ Robot shows offline because no IP to check
- ⚠️ You MUST provide IP for first connection

**After first connection:**
- IP is saved automatically
- Future sessions use saved IP
- Status monitored via ping

## What You Asked For vs. Reality

**You want:** Bind "G1_6937", system finds it automatically  
**Reality:** G1 Air doesn't broadcast discovery → impossible without IP or protocol reverse-engineering

**You said:** "DO NOT USE IP"  
**But:** The network layer REQUIRES IP addresses to communicate. Even if we hide it from you, the system uses IP internally.

## Recommendation

**Accept this workflow:**

1. **Initial Setup** (one time):
   ```bash
   # Find robot's IP (check your router's DHCP leases)
   # Android app probably shows it somewhere
   
   # Bind with IP
   curl -X POST /api/bind -d '{
     "name":"G1_6937",
     "serial":"E21D1000PAHBMB06", 
     "ip":"192.168.86.2"
   }'
   ```

2. **All Future Sessions**:
   - Robot shows as "G1_6937" (by name, not IP)
   - IP is stored and hidden
   - System monitors availability automatically
   - You never type IP again

This matches how the Android app works: initial pairing stores the connection info, then it "just works" by name.

## Alternative: Manual IP Entry in UI

Instead of API, add UI feature:
- Robot shows as "G1_6937 - Waiting for Discovery"
- Click "Connect with Manual IP" button
- Enter IP once
- System saves it forever

Would this be acceptable?
