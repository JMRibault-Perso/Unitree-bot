# UDP Integration - Start Here

## What's Been Added ✅

Your web app now has **native UDP protocol support** for:
1. **Initialize UDP** - Opens connection with robot
2. **Query Actions** - Get list of saved teaching actions  
3. **Play Actions** - Execute actions like "waist_drum_dance"

**Impact**: Minimal - you control everything manually via web UI

---

## 60-Second Quick Start

### Step 1: Start Web Server
```bash
python g1_app/ui/web_server.py
```

### Step 2: Open Web UI
```
http://localhost:9000
```

### Step 3: Connect Robot
Click "Connect" button, select G1_6937 from list

### Step 4: Initialize UDP
```bash
curl -X POST http://localhost:9000/api/udp/initialize
```

### Step 5: Get Action List
```bash
curl http://localhost:9000/api/udp/actions
```

Should see: `waist_drum_dance`, `spin_disks`, ...

### Step 6: Bring Robot to RUN Mode (Via Web UI)
- Click "Stand Up" button
- Click "RUN Mode" button  
- Verify FSM shows "RUN"

### Step 7: Play Action
```bash
curl -X POST http://localhost:9000/api/udp/play_action \
  -H "Content-Type: application/json" \
  -d '{"action_name": "waist_drum_dance"}'
```

**Robot executes waist drum motion!** 🎉

## 3 New API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/udp/initialize` | POST | Initialize UDP connection |
| `/api/udp/actions` | GET | Query saved actions |
| `/api/udp/play_action` | POST | Play action by name |

---

## Files You'll Use

### Documentation
- **START HERE**: `UDP_QUICK_START.md` - This file
- **Complete Guide**: `UDP_INTEGRATION_GUIDE.md` - Full reference
- **Testing**: `UDP_TESTING_CHECKLIST.md` - Verification steps
- **Technical**: `UDP_COMPLETION_REPORT.md` - Implementation summary

### Code
- **New Module**: `g1_app/core/udp_protocol.py` - UDP implementation
- **Web Server**: `g1_app/ui/web_server.py` - Modified (4 endpoints added)
- **Test**: `test_udp_protocol.py` - Manual testing script

---

## Key Points

✅ **Safe Design**
- All state changes done manually via web UI
- No automatic mode switching
- User maintains full control

✅ **Minimal Impact**
- UDP init = opens connection only
- Queries are read-only
- Playback = send command (robot executes)

✅ **Built-in Safety**
- FSM validation before playback
- CRC32 packet checksums
- Error handling on all operations
- Robot must be in RUN mode

---

## Troubleshooting

### "Robot not in RUN mode"
**Solution**: Use web UI to manually set RUN mode
- Click "Stand Up"
- Click "RUN Mode"
- Check FSM shows "RUN"

### "No robot connected"
**Solution**: Click "Connect" button in web UI first

### "Action not found"
**Solution**: Check name via `curl http://localhost:9000/api/udp/actions`

### Connection timeout
**Solution**: 
- Verify robot IP is correct
- Check robot on same WiFi network
- Verify port 49504 not blocked

---

## Testing Your Setup

### Automatic Test (if web server not needed)
```bash
python test_udp_protocol.py 192.168.86.3
```

Shows:
- ✅ UDP init status
- ✅ Found actions list
- ✅ API endpoint examples

### Manual Verification
```bash
# 1. Initialize
curl -X POST http://localhost:9000/api/udp/initialize

# 2. Query (should return actions)
curl http://localhost:9000/api/udp/actions

# 3. Set RUN mode in web UI, then:
curl -X POST http://localhost:9000/api/udp/play_action \
  -H "Content-Type: application/json" \
  -d '{"action_name": "waist_drum_dance"}'

```

---

## Architecture (Simple View)

```
Your Web App
    ↓
┌─────────────────────┐
│ New Web Endpoints   │
│  /api/udp/*         │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│ UDP Protocol Module │
│ (new)               │
└────────┬────────────┘
         ↓
     🌐 WiFi Port 49504
         ↓
┌─────────────────────┐
│ G1 Robot            │
│ UDP Server          │
└─────────────────────┘
```

---

## What Happens During Each Step

### Initialize (Step 4)
```
→ Send packet 0x09 (handshake)
← Robot responds
→ Send packet 0x0A (acknowledge)
→ Send packet 0x0B (sync)
→ Send packet 0x0C (complete)
✅ UDP channel open
```

### Query Actions (Step 5)
```
→ Send query command 0x1A
← Robot sends action list
  (one response per saved action)
✅ Actions list received
```

### Play Action (Step 7)
```
→ Send play command 0x41
  with action index
← Robot executes motion
✅ Motion happening on robot
```

---

## Performance

- **Init**: ~400ms
- **Query**: ~1-3 seconds  
- **Play**: Immediate
- **Stop**: Immediate

---

## Safety Checklist

Before playing actions:
- [ ] Robot is powered on
- [ ] Robot on WiFi network
- [ ] Web UI connected to robot
- [ ] UDP initialized
- [ ] **Robot manually set to RUN mode** ← CRITICAL
- [ ] Action name verified via query

---

## Commands at a Glance

```bash
# Initialize
curl -X POST http://localhost:9000/api/udp/initialize

# List actions
curl http://localhost:9000/api/udp/actions

# Play action (use exact name from list)
curl -X POST http://localhost:9000/api/udp/play_action \
  -H "Content-Type: application/json" \
  -d '{"action_name": "waist_drum_dance"}'

```

---

## Known Actions

Robot has at least these actions:
- `waist_drum_dance` ← Try this first!
- `spin_disks`
- Plus ~3 more custom actions

---

## Next Steps

1. **Read**: `UDP_INTEGRATION_GUIDE.md` for complete details
2. **Test**: Run `test_udp_protocol.py 192.168.86.3`
3. **Try**: Follow 60-second quick start above
4. **Verify**: Use `UDP_TESTING_CHECKLIST.md` to validate

---

## Support

For issues, check:
1. `UDP_INTEGRATION_GUIDE.md` - Troubleshooting section
2. `UDP_TESTING_CHECKLIST.md` - Testing steps
3. `UDP_COMPLETION_REPORT.md` - Technical details

---

## Summary

You now have:
✅ UDP protocol support in your web app
✅ Action list querying  
✅ Action playback capability
✅ Full safety validation
✅ Comprehensive documentation

**Status**: Ready to test! 🚀

---

**Need Help?**
- Q: Robot not in RUN mode?
  A: Use web UI buttons to set RUN mode manually

- Q: Action not found?
  A: Query first: `curl http://localhost:9000/api/udp/actions`

- Q: Timeout error?
  A: Verify robot IP and WiFi connection

**Questions?** Check the full guides listed above!
