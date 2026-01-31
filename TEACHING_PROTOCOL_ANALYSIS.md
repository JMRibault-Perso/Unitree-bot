# G1 Air Teaching Mode Protocol - PCAP Analysis Results

## Summary

This document is aligned to the latest PCAP (PCAPdroid_30_Jan_18_26_35.pcap). The teaching protocol is a **custom binary UDP command stream (0x17)** with confirmed commands:

- Init sequence: 0x09, 0x0A, 0x0B, 0x0C
- Action list: 0x1A (response 233 bytes)
- Teach mode: 0x0D (enter/keep‑alive), 0x0E (exit)
- Record toggle: 0x0F
- Save action: 0x2B
- Play action: 0x41

Unknown/predicted commands are intentionally excluded.

For full packet layouts and offsets, see [PCAPdroid_30_Jan_Analysis_COMPLETE.md](PCAPdroid_30_Jan_Analysis_COMPLETE.md).

## Protocol Overview

### Command Structure (57+ bytes)
```
Offset  Size  Content
------  ----  -------
0x00    4     Header: 17 FE FD 00
0x04    2     Flags (01 00)
0x06    2     Sequence counter (big‑endian)
0x08    2     Reserved: 00 00
0x0A    2     Reserved: 00 01
0x0C    1     Command ID (e.g., 0x09, 0x1A, 0x2B)
0x0D    2     Payload length (big‑endian)
0x0F    N     Payload
...     4     CRC32 (last 4 bytes)
```

## Confirmed Commands from PCAP

### Teaching Mode Commands (PCAPdroid_30_Jan_18_26_35.pcap)

| CmdID | Name | Function |
|------:|------|----------|
| 0x09 | Control Mode | Enable command interface |
| 0x0A | Param Sync | Sync parameters |
| 0x0B | Status Subscribe | Subscribe to status updates |
| 0x0C | Ready Signal | Ready flag |
| 0x0D | Enter Teach | Enter zero‑gravity mode + keep‑alive |
| 0x0E | Exit Teach | Exit teach mode |
| 0x0F | Record Toggle | Start/stop recording |
| 0x1A | List Actions | Query saved actions (233‑byte response) |
| 0x2B | Save Action | Save recorded trajectory |
| 0x41 | Play Action | Execute saved action |

## Why Robot Doesn’t Respond

The robot only responds to the teaching UDP port **while teach mode is active** and when no other client is connected. This matches the Jan 30 PCAP session behavior.

## Implementation Status

- ✅ Command list verified from the Jan 30 PCAP
- ✅ Packet layout and offsets documented in [PCAPdroid_30_Jan_Analysis_COMPLETE.md](PCAPdroid_30_Jan_Analysis_COMPLETE.md)
- ✅ UDP client code exists in `g1_app/core/udp_protocol.py`

## Next Steps

1. Connect to the robot (only one client)
2. Run the UDP teach‑mode workflow (0x09→0x0C, 0x1A, 0x0D/0x0F/0x2B/0x41, 0x0E)
3. Validate action list parsing using the 233‑byte response layout

## References

- PCAP file: `PCAPdroid_30_Jan_18_26_35.pcap`
- Analysis: [PCAPdroid_30_Jan_Analysis_COMPLETE.md](PCAPdroid_30_Jan_Analysis_COMPLETE.md)
