# Quick Start: SLAM Navigation

## What's New

Your G1 Robot Controller now has full **autonomous navigation** capabilities:

✅ Load saved SLAM maps from robot storage  
✅ Send robot to specific coordinates automatically  
✅ Pause/Resume navigation during movement  
✅ Click on 3D point cloud to set navigation goals  
✅ Real-time navigation status monitoring  

## Getting Started (5 Minutes)

### 1. Start the Web Server
```bash
cd /root/G1/unitree_sdk2
python3 -m g1_app.ui.web_server
```

Server runs on `http://localhost:9000`

### 2. Connect to Robot
- Open http://localhost:9000 in browser
- Enter robot IP (e.g., 192.168.86.4)
- Click **"Connect"**

### 3. Load a Map
1. Scroll down to **"🎯 Navigation & Map Management"** panel
2. Select **"Test Map 1"** from dropdown
3. Click **"📁 Load Map"**
4. Wait for ✅ "Map loaded successfully!"

### 4. Navigate
**Method 1: Manual Coordinates**
1. Enter X=1, Y=0, Z=0
2. Click **"🎯 Navigate To Goal"**
3. Robot moves to target

**Method 2: Click on Map**
1. Hold **Ctrl** and click on 3D point cloud above
2. Coordinates populate automatically
3. Click **"🎯 Navigate To Goal"**

### 5. Control Movement
- **Pause**: Click **"⏸️ Pause"** (robot stops)
- **Resume**: Click **"▶️ Resume"** (robot continues)

## Navigation Constraints

| Limit | Value | Notes |
|-------|-------|-------|
| Max Distance | 10m | Per navigation command |
| Obstacle Height | 50cm+ | For detection |
| Map Size | < 45m x 45m | Recommended |
| Environment | Indoor, static | Works best with features |

## Status Indicators

| Status | Meaning | Action |
|--------|---------|--------|
| **Navigating** (Green) | Robot moving to goal | Wait or pause |
| **Paused** (Yellow) | Navigation paused | Click resume to continue |
| **Idle** (Red) | No active navigation | Load a map first |
| **Error** | Something went wrong | Check connection & map |

## Keyboard Shortcuts (While Focused)

| Key | Action |
|-----|--------|
| Ctrl+Click (3D Map) | Set navigation goal |
| W/A/S/D | Manual movement |
| Space | Stop robot |

## Available Maps

Standard map slots on robot:
- test1.pcd ← Best to start here
- test2.pcd
- test3.pcd
- ... up to test10.pcd

Maps are stored in `/home/unitree/` on robot.

## Common Tasks

### Task: Navigate Robot in Square Pattern
```
1. Load map (test1.pcd)
2. Send goal: (1, 0, 0)    - Move forward
3. Send goal: (1, 1, 0)    - Move right
4. Send goal: (0, 1, 0)    - Move back
5. Send goal: (0, 0, 0)    - Return to start
```

### Task: Click-to-Navigate Workflow
```
1. Load map (test1.pcd)
2. Click 3D point cloud while holding Ctrl
3. Coordinates fill in automatically
4. Click Navigate
5. Robot goes there!
```

### Task: Pause and Resume
```
1. Send navigation goal
2. Watch robot move
3. If you need to pause: Click "Pause"
4. Robot stops where it is
5. Click "Resume" to continue
```

## Troubleshooting

### Q: "Not connected" error
**A:** Ensure robot connection in main status panel

### Q: Can't click on 3D map
**A:** Hold **Ctrl** key, not Alt or Cmd

### Q: "Failed to load map"
**A:** Try different map number (test2, test3, etc.)

### Q: Robot doesn't move
**A:** 
1. Verify SLAM mapping is active (3D point cloud shows points)
2. Check robot battery level
3. Restart robot and try again

### Q: Page shows old data
**A:** Hard refresh: **Ctrl+Shift+R** (or Cmd+Shift+R on Mac)

## Under the Hood

### API Endpoints

```
GET  /api/slam/maps                  - List available maps
POST /api/slam/load_map              - Load map for navigation
POST /api/slam/navigate_to           - Send robot to coordinates
POST /api/slam/pause_navigation      - Pause movement
POST /api/slam/resume_navigation     - Resume movement
GET  /api/slam/navigation_status     - Get current status
```

### Status Polling

Status updates automatically every 2 seconds showing:
- Loaded map name
- Current navigation goal
- Navigation active/paused/idle status
- Latest SLAM trajectory point

## Advanced: Custom Maps

To create your own map:

1. Start SLAM mapping in web UI
2. Let robot scan area
3. Click "Stop Mapping"  
4. Map saves to `/home/unitree/temp_map.pcd`
5. Rename to one of the test slots for navigation

## Performance

| Metric | Value |
|--------|-------|
| Navigation range | Up to 10m |
| Update frequency | Every 200ms |
| Command latency | 100-200ms |
| Network usage | ~0.25 KB/s |

## Next Steps

1. ✅ **Test with your robot** - Load a map and navigate!
2. 📍 **Mark key locations** - Remember coordinates for common spots
3. 🗺️ **Create custom maps** - Map your environment
4. 🤖 **Automate routines** - Queue navigation goals

## Need Help?

1. Check [SLAM_NAVIGATION_IMPLEMENTATION.md](SLAM_NAVIGATION_IMPLEMENTATION.md) for detailed docs
2. Review server logs: `tail -f /tmp/web_server.log`
3. Test API manually:
   ```bash
   curl http://localhost:9000/api/slam/maps | python3 -m json.tool
   ```

---

**Happy navigating!** 🤖✨

Your G1 can now explore autonomously!
