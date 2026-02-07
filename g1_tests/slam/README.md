# SLAM Tests

SLAM (Simultaneous Localization and Mapping) tests for mapping, navigation, and obstacle avoidance.

## 🗂️ Available Tests

### Core SLAM Workflow
- `test_slam_workflow.py` - Complete workflow: start mapping → save → load → verify
- `test_navigation_v2.py` - Navigation with obstacle avoidance
- `stop_slam_v2.py` - Quick command to close SLAM system
- `cancel_navigation_v2.py` - Pause/cancel navigation

### Map Management
- `test_map_loader.py` - Load and verify saved maps
- `test_map_viewer.py` - Visualize map point clouds

## 🎯 SLAM API Reference

| API ID | Name | Description |
|--------|------|-------------|
| 1801 | START_MAPPING | Begin SLAM mapping mode |
| 1802 | STOP_MAPPING | Stop mapping and finalize |
| 1803 | SAVE_MAP | Save current map to file |
| 1804 | LOAD_MAP | Load map with initial pose |
| 1102 | NAVIGATE | Navigate to target (includes obstacle avoidance) |
| 1201 | PAUSE_NAV | Pause current navigation |
| 1202 | RESUME_NAV | Resume paused navigation |
| 1901 | CLOSE_SLAM | Shutdown SLAM system |

## 📝 Quick Commands

### Start Mapping
```bash
python3 quick_commands/start_mapping.py
```

### Navigate to Position
```bash
python3 test_navigation_v2.py --target-x 1.0 --target-y 0.0 --target-yaw 0.0
```

### Stop SLAM
```bash
python3 stop_slam_v2.py
```

## 🚨 Important Notes

- **Map files**: Stored in `../../data/test_maps/`
- **Distance limit**: Navigation targets must be <10m
- **Obstacle detection**: LiDAR detects obstacles ≥50cm height
- **Prerequisites**: Robot must be in DAMP/READY/RUN FSM state
- **Odometry**: Subscribe to `rt/lf/sportmodestate` for position tracking

## 🔍 Troubleshooting

**"Path planning failed"**
- Check map is loaded (API 1804)
- Verify target is <10m away
- Ensure clear line of sight to target

**"Invalid FSM state"**
- Robot must be in DAMP, READY, or RUN state
- Use motion tests to set FSM state first

**Navigation doesn't start**
- Verify SLAM system initialized (API 1801 or 1804)
- Check odometry topic is publishing
