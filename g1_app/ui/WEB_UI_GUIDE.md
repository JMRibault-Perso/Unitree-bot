# G1 Web UI - Simple FSM State Machine Controller

## 🎉 Web UI is Running!

The web UI server is now running at: **http://localhost:8000**

## Features

✅ **Connection Management**
- Enter robot IP and serial number
- Connect/disconnect with visual feedback
- Real-time connection status

✅ **FSM State Visualization**
- See current FSM state and LED color
- Visual LED color indicator
- Real-time state updates via WebSocket

✅ **State Machine Control**
- Click buttons to transition between states
- Only valid transitions are enabled (grayed out = invalid)
- Current state highlighted in purple
- State validation prevents invalid commands

## Quick Start

### 1. Open the Web UI

Open your browser and go to: **http://localhost:8000**

Or from the terminal:
```bash
# On the same machine
xdg-open http://localhost:8000

# From another computer on same network
http://<your-server-ip>:8000
```

### 2. Connect to Robot

1. Enter robot details (pre-filled):
   - **IP**: `192.168.86.16`
   - **Serial Number**: `E21D1000PAHBMB06`

2. Click **Connect**

3. Wait for "Successfully connected" message

### 3. Control FSM States

Once connected, you'll see:
- **Current State**: Shows active FSM state
- **LED Color**: Shows robot LED color with visual indicator
- **State Buttons**: Grid of all available FSM states

**Available States:**
- **ZERO_TORQUE (0)** - Motors off (Purple LED)
- **DAMP (1)** - Safe mode (Orange LED)
- **SIT (3)** - Sitting position (Green LED)
- **START (200)** - Ready/Standing (Blue LED)
- **LOCK_STAND (500)** - Locked standing
- **SQUAT_TO_STAND (706)** - Transition to standing
- **STAND_TO_SQUAT (707)** - Transition to squatting
- **LYING_STAND (708)** - Lying and standing mode

### 4. Transition Between States

Click any **enabled** (not grayed out) state button to transition:

**Common Workflows:**

- **Emergency Stop**: Click **DAMP** (always available)
- **Stand Up Sequence**:
  1. DAMP → START (Ready)
  2. START → SQUAT_TO_STAND
  3. Wait for completion → Returns to START

- **Sit Down Sequence**:
  1. START → SIT
  2. Or: START → STAND_TO_SQUAT

- **Safe Shutdown**:
  1. Current state → DAMP
  2. DAMP → ZERO_TORQUE (if needed)

## State Transition Rules

The state machine enforces valid transitions based on the official G1 state diagram:

```
ZERO_TORQUE ──> DAMP ──> START ──┬──> SQUAT_TO_STAND ──> START
                                  │
                                  └──> SIT
                                       │
                                       └──> STAND_TO_SQUAT ──> SIT
```

**Emergency Transitions** (always allowed):
- Any state → **DAMP**
- Any state → **ZERO_TORQUE**

Invalid transitions will be **grayed out** and cannot be clicked.

## Real-Time Updates

The UI uses WebSocket for real-time updates:
- State changes appear immediately
- LED color updates in real-time
- Connection status updates
- No need to refresh page

## Troubleshooting

### Connection Fails

1. **Check robot is on and WiFi connected**
   ```bash
   ping 192.168.86.16
   ```

2. **Verify with Android app first**
   - Robot should show as "online" (green)

3. **Check server logs**
   - Look at terminal where web_server.py is running
   - Should see debug messages

### State Transition Rejected

- **Check valid transitions**: Only enabled buttons can be clicked
- **Current state displayed**: Highlighted in purple
- **Error message**: Shows why transition failed

### WebSocket Disconnected

- **Auto-reconnects**: Happens automatically every 2 seconds
- **Refresh page**: If issues persist, refresh browser

## Server Management

### Start Server
```bash
cd /root/G1/unitree_sdk2
python3 g1_app/ui/web_server.py
```

### Stop Server
```
Press Ctrl+C in terminal
```

Or:
```bash
pkill -f "python3 g1_app/ui/web_server.py"
```

### View Logs
Server logs appear in the terminal where you started it:
- **INFO**: Connection events, state changes
- **DEBUG**: Detailed WebSocket messages
- **ERROR**: Connection failures, invalid transitions

## Architecture

**Backend (FastAPI)**:
- REST API for commands (`/api/connect`, `/api/set_state`)
- WebSocket for real-time updates (`/ws`)
- Integrates with `RobotController` class
- Validates state transitions

**Frontend (HTML/CSS/JS)**:
- Single-page application
- Real-time WebSocket updates
- Visual state machine display
- Responsive design

**Communication Flow**:
```
Browser ──REST API──> FastAPI Server ──> RobotController ──WebRTC──> G1 Robot
        <──WebSocket── EventBus <────────┘
```

## Next Steps

### Add Motion Control
- Forward/backward walking
- Turning left/right
- Speed control slider

### Add Gestures
- Pre-programmed arm actions
- Wave, shake hands, etc.

### Add Sensor Display
- Video stream
- LiDAR point cloud
- Odometry tracking

See [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for adding features.

## API Endpoints

**REST API:**
- `POST /api/connect?ip=<ip>&serial_number=<sn>` - Connect to robot
- `POST /api/disconnect` - Disconnect from robot
- `POST /api/set_state?state_name=<STATE>` - Change FSM state
- `GET /api/state` - Get current state and allowed transitions

**WebSocket:**
- `WS /ws` - Real-time updates
  - `state_changed` - FSM state changed
  - `connection_changed` - Connection status changed

## Files

```
g1_app/ui/
├── __init__.py
├── web_server.py       # FastAPI backend
└── index.html          # Frontend UI

run_web_ui.sh           # Launch script
```

## Credits

Built with:
- **FastAPI** - Backend web framework
- **Uvicorn** - ASGI server
- **WebSockets** - Real-time communication
- **Vanilla JavaScript** - No frontend framework needed
- **G1 App Core** - Robot control library
