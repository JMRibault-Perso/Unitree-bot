# New G1 Robot Controller UI - Design Guide

**Date**: February 5, 2026  
**File**: `g1_app/ui/index_new.html`  
**Status**: ✨ Modern, organized layout with sidebar navigation

## 🎨 Layout Architecture

```
┌─────────────────────────────────────────────────────┐
│                  TOP BAR                            │
│  Robot Name | FSM State | Battery | Connect Btn    │
├──────────────────┬──────────────────────────────────┤
│                  │                                  │
│    SIDEBAR       │         MAIN CONTENT             │
│  - Connection    │  ┌────────────────┬────────────┐ │
│  - Movement      │  │                │  CONTROLS  │ │
│  - SLAM Teach    │  │   Current      │  - FSM     │ │
│  - Navigate      │  │   View Panel   │  - WASD    │ │
│  - Teach Action  │  │                │  - QE      │ │
│  - Gestures      │  │                │  - Space   │ │
│  - Status        │  │                │            │ │
│                  │  └────────────────┴────────────┘ │
└──────────────────┴──────────────────────────────────┘
```

## 📁 Component Breakdown

### Left Sidebar (280px)
- **Header**: Shows connection status with visual indicator
- **Navigation Sections**:
  - **Connection**: Quick connect button
  - **Movement**: Primary movement control
  - **SLAM & Navigation**: Map teaching and navigation
  - **Actions**: Custom action teaching and pre-built gestures
  - **Settings**: Robot status and diagnostics

### Top Bar
- Robot name/identifier
- Quick status display (FSM state, battery level)
- Connection button (changes based on state)

### Main Content Area (2-column layout)
- **Left Column**: Dynamic view panels that change based on sidebar selection
  - Movement Control
  - SLAM Teach
  - Navigation
  - Teach Action
  - Gestures
  - Status Display
  
- **Right Column**: Always-visible controls
  - FSM state buttons (never disappear)
  - WASD/QE keyboard controls
  - Emergency stop button

## 🎯 Key Features

### 1. **Sidebar Navigation**
```
✅ Always visible on desktop
✅ Easy switching between features
✅ Visual indicator of active view
✅ Organized into logical sections
```

### 2. **Always-Available Movement Controls (Right Panel)**
```
FSM States (6 buttons):
  ┌─────────────┬──────────┐
  │Zero Torque  │  Damp    │
  ├─────────────┼──────────┤
  │Start        │  Sit     │
  ├─────────────┼──────────┤
  │Squat→Stand  │Stand→Squat
  └─────────────┴──────────┘

Movement Grid (WASD):
      W
    A S D
    
Rotation (QE):
  Q (rotate left) | E (rotate right)
  
Emergency:
  STOP button (red, always accessible)
```

### 3. **Dynamic Views**

#### Movement Control
- Visual WASD grid
- Rotation controls (Q/E)
- Visual feedback on key press
- Emergency stop button
- Instructions

#### SLAM Teach Mode
- Map name input
- SLAM type selection
- Start/Stop mapping buttons
- Real-time feedback

#### Navigation
- Map selector (dropdown)
- Waypoint/coordinate input
- Navigate button
- Status feedback

#### Teach Action
- Action name input
- Record button (red, indicates recording)
- Stop button
- Status display

#### Gestures
- Grid of pre-programmed gestures
- Quick access buttons
- Visual feedback

#### Status Display
- Detailed robot information
- Battery/temperature graphs
- Network status
- Sensor data

## 🎨 Design Decisions

### Color Scheme (Dark Mode)
- **Background**: Dark gray/blue (`#0f1419`)
- **Primary**: Purple/blue gradient (`#667eea`, `#764ba2`)
- **Accent**: Green for success (`#48bb78`)
- **Error**: Red (`#f56565`)
- **Neutral**: Gray tones for text and borders

### Interactive Feedback
- **Hover**: Lighter background + blue border
- **Active**: Gradient fill + glow effect
- **Pressed**: Slightly darker, scale down
- **Disabled**: Reduced opacity, cursor disabled

### Keyboard Integration
- WASD always works when robot is connected
- Visual button feedback matches key press
- Space bar = Emergency stop
- Keys are prioritized (continuous movement processing)

## 📱 Responsive Design

### Desktop (1024px+)
- Full sidebar visible
- 2-column content layout
- All features accessible

### Tablet/Mobile (<1024px)
- Sidebar hidden (can be toggled with hamburger menu - not yet implemented)
- Single column layout
- Movement controls still accessible

## 🔧 Implementation Notes

### Current State
- ✅ HTML structure complete
- ✅ CSS styling complete
- ✅ Basic JavaScript framework in place
- ⚠️ API integration points defined (need backend updates)

### Next Steps
1. **Backend Integration**
   - Verify all `/api/` endpoints exist
   - Ensure WebSocket sends proper data format
   - Add SLAM endpoints (1801-1806)
   - Add action teaching endpoints (7107-7114)

2. **Gesture Gallery**
   - Populate gesture list from API
   - Add gesture preview images/animations
   - Add execution with single click

3. **Map Management**
   - Fetch available maps from robot
   - Display map selector
   - Add waypoint selection UI

4. **Real-time Features**
   - Add SLAM visualization (3D points)
   - Add pose tracking display
   - Add movement feedback visualization

5. **Polish**
   - Add notification system
   - Add loading spinners
   - Add confirm dialogs for destructive actions
   - Add keyboard help overlay

## 📋 API Endpoints Referenced

```javascript
// Connection
POST /api/connect?ip=X&serial_number=Y
POST /api/disconnect

// Movement
POST /api/move?vx=X&vy=Y&vyaw=Z
POST /api/stop

// FSM
POST /api/set_state?state_name=STATE

// SLAM (needs implementation)
POST /api/slam/start_mapping
POST /api/slam/stop_mapping
POST /api/slam/navigate?waypoint=X

// Actions (needs implementation)
POST /api/actions/start_teaching?name=ACTION
POST /api/actions/stop_teaching
POST /api/actions/execute?name=ACTION
```

## 🎮 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| W | Move forward |
| A | Move left |
| S | Move backward |
| D | Move right |
| Q | Rotate left |
| E | Rotate right |
| Space | Emergency stop |

## 🚀 Usage Example

1. **Connect to Robot**
   - Click "Connect Robot" in sidebar
   - Enter IP and serial number
   - Click Connect

2. **Move the Robot**
   - FSM should auto-transition through necessary states
   - Press W/A/S/D to move (or use on-screen buttons)
   - Use Q/E to rotate
   - Press Space or click STOP for emergency stop

3. **Teach a Map**
   - Click "Teach Map" in sidebar
   - Enter map name
   - Click "Start Mapping"
   - Drive robot around (use movement controls)
   - Click "Stop & Save Map"

4. **Use a Gesture**
   - Click "Gestures" in sidebar
   - Click any gesture button
   - Robot executes the gesture

5. **Record Custom Action**
   - Click "Teach Action" in sidebar
   - Enter action name
   - Click "Start Recording"
   - Drive robot/move arms (repeat the action)
   - Click "Stop Recording"
   - Action saved and can be executed later

## 💾 To Deploy

Replace current UI:
```bash
cd /root/G1/unitree_sdk2/g1_app/ui
cp index.html index_backup.html
cp index_new.html index.html
# Restart web server
```

Verify it works:
```bash
# Open http://localhost:3000 in browser
# Should see new sidebar layout
```

## 📝 Future Enhancements

- [ ] Hamburger menu for mobile
- [ ] Gesture preview images/videos
- [ ] 3D visualization of robot state
- [ ] SLAM map viewer (2D/3D)
- [ ] Voice command integration
- [ ] Touch-friendly controls for tablet
- [ ] Game controller support (Gamepad API)
- [ ] Settings/configuration panel
- [ ] Favorites/quick-access buttons
- [ ] Command history/undo
