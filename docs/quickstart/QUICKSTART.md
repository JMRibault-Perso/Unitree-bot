# QUICK START - Run SLAM Test

## ✅ Everything is Ready

Your workspace is now **clean and organized**. All test files are properly organized, old documentation archived, and SDK remains pristine.

## 🚀 Run the SLAM Test Now

```bash
# 1. Navigate to test directory
cd /root/G1/unitree_sdk2/G1_tests/slam

# 2. Run the test
python3 simple_slam_test.py
```

## 📖 Reference Docs (In Root)

- **[STATUS.md](STATUS.md)** - Current work progress
- **[G1_WEBRTC_PROTOCOL.md](G1_WEBRTC_PROTOCOL.md)** - How G1 works with WebRTC

## 🔧 What the Test Does

1. Starts SLAM mapping (you walk robot around room)
2. Saves map to `/home/unitree/test_simple.pcd`
3. Loads the map back
4. Monitors robot poses for 15 seconds
5. Tests navigation to target position
6. Closes SLAM cleanly

**Expected Output:**
```
✅ PHASE 1: START MAPPING
✅ PHASE 2: SAVE MAP
✅ PHASE 3: LOAD MAP
✅ PHASE 4: MONITORING (receives pose updates)
✅ PHASE 5: NAVIGATION
✅ PHASE 6: CLOSE SLAM
✅ SLAM TEST COMPLETE
```

## 🎯 Success Criteria

Test passes when you see:
- ✅ Map file created: `/home/unitree/test_simple.pcd`
- ✅ Pose updates printed to console (>10 messages)
- ✅ Final "✅ SLAM TEST COMPLETE" message

## ⚠️ Before Running

Make sure:
- [ ] Robot is powered on (green WiFi indicator)
- [ ] PC connected to same WiFi as robot
- [ ] g1_app web server is NOT running (only one WebRTC client)

**Stop the server if it's running:**
```bash
pkill -f "python3 g1_app"
```

## 📚 Learn More

Once the test works:
1. Read [G1_WEBRTC_PROTOCOL.md](G1_WEBRTC_PROTOCOL.md) to understand the protocol
2. Check [STATUS.md](STATUS.md) for what's done and what's next
3. Modify test for your own experiments (change coordinates, etc.)

---

**That's it. Clean workspace. Clear docs. Ready to go.** 🎉
