# Robot Discovery - Single Source of Truth

**Last Updated**: February 5, 2026

## ⚠️ IMPORTANT: Use Only This Method

All robot discovery in this codebase now uses **one centralized approach**:

```python
from g1_app.utils.robot_discovery import discover_robot

robot = discover_robot()
if robot and robot['online']:
    print(f"Robot at {robot['ip']} - Mode: {robot['mode']}")
```

## Why Centralized Discovery?

Previously, different scripts used different discovery methods:
- ❌ Old `discover_robot_ip()` with complex cascading (slow, unreliable)
- ❌ Direct ARP parsing without ping verification (stale cache issues)
- ❌ Multicast-only (doesn't work when robot doesn't broadcast)
- ❌ Manual ping scripts

**Now**: Everything uses the proven web server discovery logic:
1. Try multicast (231.1.1.2:7400) - 0.5s timeout
2. Fall back to ARP with ping verification - catches stale entries
3. Return online/offline status + network mode

## API Reference

### `discover_robot(target_mac=G1_MAC, verify_with_ping=True)`

Discover robot using web server's proven method.

**Returns**:
```python
{
    'ip': '192.168.86.2',
    'mac': 'fc:23:cd:92:60:02',
    'mode': 'STA-L',  # AP, STA-L, or STA-T
    'online': True     # ping verified
}
# or None if not found
```

**Example**:
```python
from g1_app.utils.robot_discovery import discover_robot

robot = discover_robot()
if not robot:
    print("Robot not found")
elif not robot['online']:
    print(f"Robot at {robot['ip']} is OFFLINE")
else:
    print(f"Robot ONLINE at {robot['ip']}")
    # Use robot['ip'] for WebRTC connection
```

### `wait_for_robot(target_mac=G1_MAC, timeout=30, check_interval=2)`

Wait for robot to boot and come online.

**Example**:
```python
from g1_app.utils.robot_discovery import wait_for_robot

print("Waiting for robot to boot...")
robot = wait_for_robot(timeout=60)  # Wait up to 60 seconds
if robot:
    print(f"Robot ready at {robot['ip']}")
```

## Migration Guide

### Old Code (DON'T USE):
```python
# ❌ DEPRECATED
from g1_app.utils.arp_discovery import discover_robot_ip
ip = discover_robot_ip(fast=True)
```

### New Code (USE THIS):
```python
# ✅ CORRECT
from g1_app.utils.robot_discovery import discover_robot
robot = discover_robot()
if robot and robot['online']:
    ip = robot['ip']
```

## Network Modes

| Mode | Description | IP Range |
|------|-------------|----------|
| **AP** | Robot is WiFi hotspot | 192.168.12.1 |
| **STA-L** | Same local network | 192.168.x.x (your network) |
| **STA-T** | Remote network (cloud) | Different subnet |

## Performance

- **Online detection**: 2-4 seconds (multicast + ARP)
- **Offline detection**: 3-5 seconds (ping timeout + missed scan)
- **Scan interval**: 2 seconds (web server)
- **No stale ARP cache issues**: Ping verification on every scan

## Files Updated

**Core Discovery**:
- ✅ `g1_app/utils/robot_discovery.py` - **SINGLE SOURCE OF TRUTH**
- ✅ `g1_app/core/robot_discovery.py` - Web server uses this
- ✅ `g1_tests/robot_test_helpers.py` - All test scripts use this

**Deprecated** (kept for reference):
- ⚠️ `g1_app/utils/arp_discovery.py` - Legacy, use only for low-level functions
- ⚠️ `ENHANCED_DISCOVERY_*.md` - Old documentation, archived

## Testing

Verify discovery works:
```bash
cd /root/G1/unitree_sdk2
python3 -c "
from g1_app.utils.robot_discovery import discover_robot
robot = discover_robot()
print(f'Robot: {robot}')
"
```

Monitor real-time discovery:
```bash
cd g1_tests && python3 test_discovery_monitor.py
```

## Troubleshooting

**Robot shows offline but is powered on?**
- Check network connection: `ping 192.168.86.2`
- Verify MAC address: `arp -n | grep fc:23:cd:92:60:02`
- Check firewall allows ICMP ping

**Discovery too slow?**
- Multicast should find robot in 0.5s
- If ARP fallback triggers, check multicast support on network
- Web server scans every 2 seconds

**"Robot not found"?**
1. Verify robot is on same WiFi network
2. Check IP with Android app
3. Try direct IP: `discover_robot()` falls back to ARP

## Web Server Integration

The web server at `g1_app/ui/web_server.py` uses the same discovery logic in its background loop. Your scripts and the web UI will always agree on robot status.

Access web UI:
```
http://localhost:3000
```

Check API:
```bash
curl http://localhost:3000/api/discover
```

---

**Bottom Line**: Always use `from g1_app.utils.robot_discovery import discover_robot` for robot discovery. Everything else is deprecated or internal implementation details.
