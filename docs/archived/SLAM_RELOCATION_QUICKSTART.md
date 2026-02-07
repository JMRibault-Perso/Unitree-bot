# SLAM Relocation Testing - Quick Start

## You Now Have

✅ **room.pcd map** - Reusable map built and verified on robot
✅ **test_relocation.py** - Real-time position monitor for relocation testing  
✅ **check_slam_topics.py** - Diagnostic tool to verify topics publishing
✅ **Web API endpoint** - `/api/slam/current_position` for programmatic access
✅ **RobotController tracking** - Automatic position update collection
✅ **Complete testing guide** - SLAM_RELOCATION_TESTING.md

## Run the Test

```bash
cd /root/G1/unitree_sdk2/G1_tests/slam
python3 test_relocation.py
```

Then **move your robot around for 60 seconds** and watch position updates.

## What You'll See

Real-time position display:
```
📍 X=   1.234m  Y=   0.567m  Z=   0.000m  Heading= 45.2°  ΔDist= 1.389m  Updates=  120
```

Summary at the end:
```
✅ RELOCATION WORKING
   - Robot received 1200 position updates
   - Movement detected:
     - Robot moved 2.567m
     - Heading changed 45.2°
```

## Next: Verify Relocation Works

1. **Quick check:** Is relocation active?
   ```bash
   python3 check_slam_topics.py
   # Should show updates on rt/unitree/slam_relocation/odom
   ```

2. **Full test:** Load map and move robot
   ```bash
   python3 test_relocation.py
   # Move robot around for 60 seconds
   # Position should update in real-time
   ```

3. **Access position programmatically:**
   ```bash
   curl http://192.168.86.2:8080/api/slam/current_position
   # Returns current position as JSON
   ```

## What This Tests

- **Map loaded correctly** - room.pcd file exists and loads
- **Relocation active** - Position updates from odometry
- **Position tracking** - X, Y, Z coordinates changing as robot moves
- **Heading tracking** - Yaw angle changing as robot rotates

## Troubleshooting

If **no position updates** (Updates = 0):
1. Check map exists: `ls -lh /home/unitree/room.pcd`
2. Check relocation topics: `python3 check_slam_topics.py`
3. Verify robot FSM state is RUN/LOCK_STAND

If **position not changing** when you move robot:
1. Move robot further (small movements may not trigger updates)
2. Try rotating robot (heading change is easier to see)
3. Check if relocation_odom topic is receiving messages

## What's Next

Once relocation is verified:
- Phase A: Create waypoint storage system (use current_position API)
- Phase B: Add waypoint CRUD endpoints
- Phase C: Implement navigation between waypoints
- Phase D: Build web UI for waypoint management
- Phase E: Persist waypoints across restart

---

**Ready to test?** Run: `python3 G1_tests/slam/test_relocation.py`
