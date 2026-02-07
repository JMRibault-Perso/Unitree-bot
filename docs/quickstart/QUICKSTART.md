# QUICK START - Run SLAM Test

## ✅ Setup Once

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
```

## 🚀 Run the SLAM Test Now

```bash
# 1. Navigate to test directory
cd g1_tests/slam

# 2. Run the test
python3 simple_slam_test.py
```

## 📖 Reference Docs

- **[Main Docs Index](../README.md)**
- **[Web UI Guide](../../g1_app/ui/WEB_UI_GUIDE.md)**

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
1. Read [docs/README.md](../README.md) to understand the system
2. Check [docs/guides/](../guides/) for workflows and testing
3. Modify test for your own experiments (change coordinates, etc.)

---

**That's it. Clean workspace. Clear docs. Ready to go.** 🎉
