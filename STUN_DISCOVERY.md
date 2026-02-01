# WebRTC/STUN Port Discovery Implementation

## Summary

Based on PCAP analysis of the Android app's teaching mode session, we discovered that the teaching protocol port is **dynamically negotiated via WebRTC/STUN**, not hardcoded.

## Key Findings from PCAP Analysis

1. **STUN Handshake First**: Android app establishes WebRTC connection using STUN protocol (packet #151)
2. **Teaching Protocol Second**: Teaching protocol starts AFTER STUN negotiation (packet #166)
3. **Dynamic Port**: Port 51639 was negotiated via STUN (not hardcoded 49504 or 43893)
4. **STUN Magic Cookie**: Packets contain `0x2112a442` (RFC 5389 STUN identifier)
5. **Attributes**: STUN Binding Requests include:
   - `USERNAME`: "n7Px:iq2R"
   - `SOFTWARE`: "Unitree Explore"
   - `FINGERPRINT` and `MESSAGE-INTEGRITY` for authentication

## Implementation: `stun_discovery.py`

### Port Discovery Strategy

The implementation uses a two-phase approach:

#### Phase 1: STUN Discovery (Proper Method)
1. Send STUN Binding Requests to robot on multiple ports:
   - 3478 (standard STUN)
   - 19302 (Google STUN)
   - 51639 (observed teaching port)
2. Parse STUN Binding Response to extract:
   - `XOR-MAPPED-ADDRESS` (preferred, RFC 5389)
   - `MAPPED-ADDRESS` (legacy)
3. Extract allocated port number from response
4. Verify port responds to teaching protocol

#### Phase 2: Fallback Port Scanning
If STUN fails (robot not responding or different implementation):
1. Try known ports: `[51639, 49504, 43893, 45559]`
2. For each port, send teaching protocol test packet (command 0x09)
3. Check for valid response starting with `17 fe fd 00`
4. Return first responding port

### Port Verification

Each discovered port is verified by:
1. Sending teaching protocol init packet (0x09)
2. Waiting for response (timeout: 1 second)
3. Validating response starts with `17 fe fd 00` (teaching protocol signature)

### Caching

Discovered ports are cached in `web_server.py`:
```python
teaching_port_cache = {}  # IP -> port mapping
```

Cache is cleared on:
- Connection errors
- Empty action list responses
- Any query failures

## Usage

### Standalone Testing
```bash
python3 g1_app/core/stun_discovery.py 192.168.86.3
```

### In Web Server
```python
from g1_app.core.stun_discovery import discover_teaching_port

# Discover port (tries STUN, then falls back to port scan)
port = discover_teaching_port(robot_ip, timeout=3.0)

# Use discovered port
if port:
    client = UDPProtocolClient(robot_ip, port)
    actions = client.query_actions()
```

### Via API
```bash
curl -X POST http://localhost:9000/api/teaching/list
```

Response includes discovered port:
```json
{
  "success": true,
  "actions": ["wave", "dance", ...],
  "count": 10,
  "port": 51639
}
```

## STUN Message Format (RFC 5389)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|0 0|     STUN Message Type     |         Message Length        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Magic Cookie (0x2112A442)             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                     Transaction ID (96 bits)                  |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Attributes                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Message Types
- `0x0001`: Binding Request
- `0x0101`: Binding Success Response

### Key Attributes
- `0x0001`: MAPPED-ADDRESS (legacy)
- `0x0020`: XOR-MAPPED-ADDRESS (preferred)
- `0x0006`: USERNAME
- `0x8022`: SOFTWARE
- `0x8028`: FINGERPRINT

## Limitations

The current G1 Air robot (without Jetson NX) may not respond to STUN queries because:
1. WebRTC/STUN might be handled internally by the robot's PC1
2. External clients may need full WebRTC signaling (not just STUN)
3. Teaching protocol port might be pre-allocated and announced differently

**Current Status**: STUN discovery times out on G1 Air. Fallback port scanning also fails because robot needs to be in specific state (teach mode enabled) to respond to teaching protocol.

## Next Steps

1. **Test during active teaching session**: Run discovery while Android app is connected and in teach mode
2. **Capture full WebRTC handshake**: Use Wireshark to capture complete signaling exchange
3. **Implement WebRTC signaling**: May need to implement full WebRTC data channel establishment
4. **Alternative discovery**: Check if robot advertises teaching port via mDNS/Bonjour

## References

- RFC 5389: Session Traversal Utilities for NAT (STUN)
- PCAP analysis: `PCAPdroid_30_Jan_18_26_35.pcap`
- Analysis tool: `analyze_teaching_port.py`
