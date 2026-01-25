# G1 Robot E21D1000PAHBMB06 - Quick Reference

## ✅ What's Working

- ✅ Robot pingable at 192.168.86.3
- ✅ Python WebRTC libraries installed
- ✅ Control scripts ready to use
- ✅ Robot serial number confirmed: **E21D1000PAHBMB06**

## 🎯 Next Step: Use Cloud Connection

Your robot's local WebRTC ports (8081, 9991) are closed, but **cloud connection works**!

### Quick Start (Cloud Mode)

```bash
cd /root/G1/unitree_sdk2
python3 g1_webrtc_controller.py
```

**Select:**
- Connection: `3` (Remote)
- Serial: `E21D1000PAHBMB06` (press Enter)
- Enter your Unitree app email
- Enter your password

This uses the same cloud API as your Android app!

## 📋 Available Scripts

| Script | Purpose |
|--------|---------|
| `g1_webrtc_controller.py` | Full interactive controller |
| `test_g1_webrtc.py` | Connection test |
| `quick_webrtc_test.sh` | Automated connection check |
| `G1_CONNECTION_STATUS.sh` | Status info & troubleshooting |
| `WEBRTC_GUIDE.md` | Complete documentation |

## 🎮 Controller Commands

Once connected in interactive mode:

**Arm Gestures:**
- `wave`, `handshake`, `high_five`, `hug`
- `clap`, `hands_up`, `xray`

**Movement:**
- `walk`, `run` (change mode)
- `forward`, `back`, `left`, `right`
- `turn_left`, `turn_right`
- `stop`, `reset`

**Control:**
- `help` (list commands)
- `quit` (exit)

## 🔧 Connection Modes Comparison

| Mode | Status | Use Case |
|------|--------|----------|
| **Remote (Cloud)** | ✅ Ready | Same as Android app, works anywhere |
| **LocalSTA** | ⚠️ Needs enabling | Direct WiFi, lower latency |
| **LocalAP** | ⚠️ Needs enabling | Robot as hotspot |

## 📝 Example: Wave Hello

```python
import asyncio
from unitree_webrtc_connect.webrtc_driver import (
    UnitreeWebRTCConnection, WebRTCConnectionMethod
)

async def wave_hello():
    # Connect via cloud
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.Remote,
        serialNumber="E21D1000PAHBMB06",
        username="your-email@example.com",
        password="your-password"
    )
    
    await conn.connect()
    print("Connected! Waving...")
    
    # Send wave command
    await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/arm/request",
        {"api_id": 7106, "parameter": {"data": 26}}  # High wave
    )
    
    await asyncio.sleep(5)
    print("Done!")

asyncio.run(wave_hello())
```

## 🚀 Why Cloud Mode is Recommended

1. **Works immediately** - no robot configuration needed
2. **Same as Android app** - uses Unitree's servers
3. **Reliable** - established connection method
4. **Remote access** - control from anywhere

## 🔐 Enabling Local WebRTC (Optional)

For direct local control without cloud:

1. **Check Android App:**
   - Settings → Developer Mode / SDK Mode
   - Enable if available
   
2. **Ask Unitree Support:**
   - Email: support@unitree.com
   - Subject: "Enable WebRTC SDK for E21D1000PAHBMB06"
   - They can guide you on enabling local access

3. **After enabling:**
   - Ports 8081 and 9991 should accept connections
   - Use LocalSTA mode with IP or serial number

## 📚 Resources

- **Documentation:** [WEBRTC_GUIDE.md](WEBRTC_GUIDE.md)
- **Library:** `/root/G1/go2_webrtc_connect/`
- **Examples:** `/root/G1/go2_webrtc_connect/examples/g1/`
- **Unitree Docs:** https://support.unitree.com/home/en/G1_developer

## 🎉 Success Path

```
1. Run: python3 g1_webrtc_controller.py
2. Select Remote mode (option 3)
3. Enter E21D1000PAHBMB06
4. Login with Unitree account
5. Type commands: wave, walk, forward, etc.
6. Enjoy controlling your G1!
```

---

**Your robot is ready for WebRTC control!** Start with cloud mode, then optionally enable local access later.
