# G1 Air Control - Quick Reference Card

## 🚀 Quick Start (30 seconds)

```bash
cd /root/G1/unitree_sdk2
python3 g1_controller.py

# Press 'd' for Damp
# Press 's' for Ready
# Press 'u' to Stand Up
```

## 🎯 THE KEY DISCOVERY

```python
# ❌ WRONG (GO2 style):
{"api_id": 1001}  # Doesn't work on G1!

# ✅ CORRECT (G1 LocoClient):
{
    "api_id": 7101,
    "parameter": json.dumps({"data": 1})
}
```

## 📊 FSM State Cheat Sheet

| Key | FSM | State | When to Use |
|-----|-----|-------|-------------|
| `z` | 0 | Zero Torque | Emergency stop |
| `d` | 1 | Damp | **START HERE** (orange LED) |
| `s` | 200 | Ready | After damp, before motion |
| `u` | 706 | Stand Up | From squat position |

## 🔌 Connection Info

- **Robot IP**: `192.168.86.16`
- **Robot SN**: `E21D1000PAHBMB06`
- **WebRTC**: Only ONE client at a time (close Android app!)

## ⚠️ Common Mistakes

1. ❌ Using GO2 commands (api_id 1001-1017) → Use FSM 7101
2. ❌ Android app still open → Close it completely
3. ❌ Wrong payload format → Use `json.dumps({"data": fsm_id})`
4. ❌ Skipping Damp mode → Always start with `d`

## 🛠️ Troubleshooting One-Liners

```bash
# Check connection
ping 192.168.86.16

# Verify robot IP on network
nmap -sn 192.168.86.0/24 | grep -A 2 "192.168.86.16"

# Check if Android app is running
# → Just close it on your phone!
```

## 💾 Backup This Command

```python
# Minimal Damp command (save this!)
payload = {
    "api_id": 7101,
    "parameter": json.dumps({"data": 1})
}
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/sport/request", payload
)
```

## 📞 When Things Go Wrong

1. **Robot not responding?**
   - LED orange after `d`? → Working!
   - No LED change? → Check Android app is closed
   
2. **Connection failed?**
   - `ping 192.168.86.16` works? → IP is correct
   - Timeout? → Robot might be asleep, use Android app to wake

3. **MediaStreamError?**
   - **Ignore it** - it's just video stream noise
   - Commands still work!

---
**TL;DR**: G1 Air needs WebRTC + API 7101 + FSM states. Start with `d` (Damp), then `s` (Ready).
