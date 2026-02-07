# SLAM Navigation Guide

## Overview

The G1 robot uses WebRTC-based SLAM (Simultaneous Localization and Mapping) for navigation, mapping, and waypoint control. This guide covers building maps, relocating within them, and navigating to waypoints.

## Quick Start

### 1. Build a Map

```bash
# Start map building session
cd slam_example && python3 build_room_map.py
```

- Use keyboard/joystick controls to drive the robot around the space
- The robot builds a 2D occupancy grid map as it moves
- Save the map when complete

### 2. Relocate in Map

```bash
# Test relocation detection
cd g1_tests && python3 test_relocation_detection.py
```

The robot must relocate (determine its position within the map) before navigating.

### 3. Navigate to Waypoints

```bash
# Navigate to a specific waypoint
cd slam_example && python3 navigate_waypoint.py --waypoint_name "kitchen"
```

## Map Building

### Using Joystick Control

```python
from g1_app.utils.robot_discovery import discover_robot
from g1_app.slam.map_builder import MapBuilder

# Discover robot
robot = discover_robot()

# Create map builder
builder = MapBuilder(robot_ip=robot['ip'])

# Start building
await builder.start_mapping()

# Drive around with joystick...

# Save map
await builder.save_map("my_room")
```

### Map File Format

Maps are saved in `data/maps/` directory with:
- `map_name.pgm` - Occupancy grid image
- `map_name.yaml` - Map metadata (resolution, origin)
- `map_name.json` - Waypoint data

## Relocation

### Automatic Relocation

```python
from g1_app.slam.relocation import wait_for_relocation

# Wait for robot to relocate
success = await wait_for_relocation(timeout=30)
if success:
    print("Robot relocated successfully")
```

### Manual Relocation Trigger

API: `1102` - Trigger relocation at specific pose

```python
await slam_client.relocate(x=0, y=0, heading=0)
```

## Navigation

### Waypoint Navigation

```python
from g1_app.slam.navigation import navigate_to_waypoint

# Navigate to named waypoint
result = await navigate_to_waypoint("kitchen")

# Or navigate to coordinates
result = await navigate_to_coordinates(x=2.0, y=1.5)
```

### Navigation Status

Subscribe to `rt/slam/navigation_status` to monitor:
- Current target waypoint
- Distance to target
- Navigation state (moving, arrived, stuck)

## Topics Reference

### SLAM Topics (WebRTC)

- `rt/lf/slam/map` - 2D occupancy grid updates
- `rt/lf/slam/pose` - Robot's current pose (x, y, heading)
- `rt/lf/slam/path` - Planned navigation path
- `rt/slam/navigation_status` - Navigation state

### SLAM APIs

- **1101**: Start mapping
- **1102**: Trigger relocation
- **1103**: Save map
- **1104**: Load map
- **1105**: Navigate to waypoint
- **1106**: Cancel navigation

## Troubleshooting

### Robot Won't Relocate

1. Ensure map is loaded
2. Verify robot is in the correct environment
3. Try moving robot to a more distinctive location
4. Check LiDAR is working (`rt/utlidar/cloud_livox_mid360` has data)

### Navigation Gets Stuck

1. Check for obstacles blocking path
2. Verify waypoint is reachable
3. Try canceling and re-navigating
4. Check navigation status topic for error details

### Map Building Quality Issues

1. Drive slower for better quality
2. Ensure good lighting for visual features
3. Close loops (return to starting position)
4. Avoid featureless areas (long blank walls)

## See Also

- [Robot Discovery API](../api/robot-discovery.md) - Finding robots on network
- [Testing Guide](testing-guide.md) - How to test SLAM features
- [Project Structure](../reference/project-structure.md) - Where SLAM code lives
