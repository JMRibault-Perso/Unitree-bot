#!/usr/bin/env python3
"""
Simple Web UI Server for G1 Robot Control
FastAPI backend with WebSocket for real-time updates
"""

import asyncio
import logging
import os
import json
import socket
import subprocess
import platform
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path for Windows compatibility
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from g1_app.utils.pathing import get_webrtc_paths

# Add WebRTC library paths (Linux and Windows)
webrtc_paths = get_webrtc_paths()

for path in webrtc_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn
import re

from g1_app import RobotController, EventBus, Events, FSMState, LEDColor
from g1_app.utils import setup_app_logging
from g1_app.core.robot_discovery import get_discovery
from g1_app.arm_controller import ArmController

# Setup logging
setup_app_logging(verbose=False)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="G1 Robot Controller")

# Mount static files directory
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"✅ Mounted static files from: {static_dir}")
else:
    logger.warning(f"⚠️ Static directory not found: {static_dir}")

# Global robot controller
robot: Optional[RobotController] = None
arm_controller: Optional[ArmController] = None
connect_lock = asyncio.Lock()
connected_clients = []

# Teach-mode recording state (API 7110)
teach_recording_task: Optional[asyncio.Task] = None
teach_recording_timeout_task: Optional[asyncio.Task] = None
teach_recording_active = False
teach_recording_name: Optional[str] = None
TEACH_RECORDING_MAX_SECONDS = 20

# Robot management
ROBOTS_FILE = Path(__file__).parent / "robots.json"

def load_robots():
    """Load robots from JSON file"""
    if ROBOTS_FILE.exists():
        try:
            with open(ROBOTS_FILE) as f:
                data = json.load(f)
                return data.get('robots', [])
        except Exception as e:
            logger.error(f"Failed to load robots: {e}")
    return []

def save_robots(robots):
    """Save robots to JSON file"""
    try:
        with open(ROBOTS_FILE, 'w') as f:
            json.dump({'robots': robots}, f, indent=2)
        logger.info(f"✅ Saved {len(robots)} robots to {ROBOTS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save robots: {e}")

def generate_robot_id(nickname):
    """Generate a unique ID from nickname"""
    return nickname.lower().replace(' ', '_')

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")


manager = ConnectionManager()


# Event handlers to broadcast to web clients
def on_state_change(state):
    """Broadcast state changes to all web clients"""
    global robot  # Need global to access robot.state_machine
    logger.info(f"📡 on_state_change called with: {state}")
    try:
        # Get allowed transitions from the robot's ACTUAL state machine
        # DO NOT create a new instance - it starts in ZERO_TORQUE!
        from g1_app.api.constants import FSMState
        
        # Ensure robot exists
        if not robot:
            logger.error("❌ on_state_change: robot is None!")
            return
        
        # Handle both dict format (from robot_controller) and state object format (from state_machine)
        if isinstance(state, dict):
            # Dictionary format from robot_controller
            fsm_state_name = state.get("fsm_state_name", "UNKNOWN")
            
            # Get allowed transitions from robot controller's state machine
            allowed = robot.state_machine.get_allowed_transitions()
            
            data = {
                "fsm_state": fsm_state_name,
                "fsm_state_value": state.get("fsm_state", 0),
                "fsm_mode": state.get("fsm_mode"),
                "led_color": "blue",  # Default, will be updated by separate LED events
                "error": None,
                "allowed_transitions": [s.name for s in allowed]
            }
        else:
            # State object format from state_machine
            allowed = robot.state_machine.get_allowed_transitions()
            
            data = {
                "fsm_state": state.fsm_state.name,
                "fsm_state_value": state.fsm_state.value,
                "fsm_mode": state.fsm_mode,
                "led_color": state.led_color.value,
                "error": state.error,
                "allowed_transitions": [s.name for s in allowed]
            }
        
        asyncio.create_task(manager.broadcast({
            "type": "state_changed",
            "data": data
        }))
        logger.info(f"📤 Broadcasting state_changed: {data.get('fsm_state')}")
    except Exception as e:
        logger.error(f"Error in on_state_change: {e}")
        logger.error(f"State data: {state}, type: {type(state)}")


def on_connection_change(data):
    """Broadcast connection status to all web clients"""
    asyncio.create_task(manager.broadcast({
        "type": "connection_changed",
        "data": data
    }))


def on_battery_update(data):
    """Broadcast battery status to all web clients"""
    try:
        asyncio.create_task(manager.broadcast({
            "type": "battery_updated",
            "data": {
                "soc": data.get("soc"),
                "voltage": data.get("voltage"),
                "current": data.get("current"),
                "temperature": data.get("temperature")
            }
        }))
    except Exception as e:
        logger.error(f"Error in on_battery_update: {e}")


def on_speech_recognized(data):
    """Broadcast speech recognition to all web clients"""
    try:
        asyncio.create_task(manager.broadcast({
            "type": "speech_recognized",
            "data": {
                "text": data.get("text"),
                "confidence": data.get("confidence"),
                "angle": data.get("angle"),
                "timestamp": data.get("timestamp")
            }
        }))
    except Exception as e:
        logger.error(f"Error in on_speech_recognized: {e}")


def on_lidar_data_received(data):
    """Store point cloud data and broadcast status to web clients"""
    print(f"DEBUG: on_lidar_data_received called, data type: {type(data)}")
    try:
        global robot
        
        if data is None:
            print("WARNING: data is None")
            logger.warning("⚠️  Received None data in on_lidar_data_received")
            return
            
        points = data.get('points', []) if isinstance(data, dict) else []
        print(f"DEBUG: Got {len(points)} points, robot={robot}")
        logger.info(f"🔵 on_lidar_data_received called with {len(points)} points")
        
        # Store the point cloud data for API endpoint
        if robot:
            # Convert to list if it's a numpy array, then copy
            if hasattr(points, 'tolist'):
                robot.latest_lidar_points = points.tolist()
            elif len(points) > 0:
                robot.latest_lidar_points = list(points)
            else:
                robot.latest_lidar_points = []
            print(f"DEBUG: Stored {len(robot.latest_lidar_points)} points in robot.latest_lidar_points")
            logger.info(f"📊 Stored {len(robot.latest_lidar_points)} points in robot.latest_lidar_points")
        else:
            print("WARNING: robot is None!")
            logger.warning("⚠️  Robot object is None, cannot store points")
            
    except Exception as e:
        print(f"ERROR in handler: {e}")
        logger.error(f"❌ Error in on_lidar_data_received: {e}", exc_info=True)


# Subscribe to events
logger.info("🔧 Setting up EventBus subscriptions...")
EventBus.subscribe(Events.STATE_CHANGED, on_state_change)
logger.info(f"  ✅ Subscribed to STATE_CHANGED")
EventBus.subscribe(Events.CONNECTION_CHANGED, on_connection_change)
logger.info(f"  ✅ Subscribed to CONNECTION_CHANGED")
EventBus.subscribe(Events.BATTERY_UPDATED, on_battery_update)
logger.info(f"  ✅ Subscribed to BATTERY_UPDATED")
EventBus.subscribe(Events.SPEECH_RECOGNIZED, on_speech_recognized)
logger.info(f"  ✅ Subscribed to SPEECH_RECOGNIZED")
EventBus.subscribe(Events.LIDAR_CLOUD, on_lidar_data_received)
logger.info(f"  ✅ Subscribed to LIDAR_CLOUD with handler: {on_lidar_data_received}")
logger.info("🔧 EventBus subscriptions complete")


@app.on_event("startup")
async def startup_event():
    """Start services on server startup"""
    logger.info("Starting robot discovery service...")
    discovery = get_discovery()
    await discovery.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on server shutdown"""
    logger.info("Stopping robot discovery service...")
    discovery = get_discovery()
    await discovery.stop()


@app.get("/api/discover")
async def discover_robots_endpoint(mac: str = None):
    """Get list of discovered robots OR discover specific robot by MAC address
    
    Args:
        mac: Optional MAC address to discover specific robot
        
    Returns:
        If mac provided: {"ip": "...", "mac": "...", "online": bool}
        If no mac: {"success": True, "robots": [...], "count": int}
    """
    logger.info(f"🔍 Discovery endpoint called (mac={mac})")
    
    # If MAC provided, do targeted discovery
    if mac:
        try:
            logger.info(f"Discovering robot with MAC: {mac}")
            from g1_app.utils.robot_discovery import discover_robot
            robot = discover_robot(target_mac=mac, verify_with_ping=True)
            
            if robot and robot.get('online'):
                logger.info(f"✅ Robot found at {robot['ip']} (online)")
                return {"ip": robot['ip'], "mac": robot['mac'], "online": True}
            elif robot and robot.get('ip'):
                logger.warning(f"⚠️ Robot found at {robot['ip']} but may be offline")
                return {"ip": robot['ip'], "mac": robot['mac'], "online": False}
            else:
                logger.error(f"❌ Robot with MAC {mac} not found on network")
                return {"ip": None, "mac": mac, "online": False, "error": "Robot not found on network"}
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            import traceback
            traceback.print_exc()
            return {"ip": None, "mac": mac, "online": False, "error": str(e)}
    
    # No MAC provided - return all robots from discovery service
    try:
        discovery = get_discovery()
        
        # Get all robots (bound + discovered)
        all_robots = discovery.get_robots()
        
        logger.info(f"Found {len(all_robots)} robots")
        
        return {
            "success": True,
            "robots": [
                {
                    "name": r.name,
                    "serial_number": r.serial_number,
                    "ip": r.ip,
                    "is_bound": True,  # All robots from get_robots() are bound
                    "is_online": r.is_online,
                    "last_seen": r.last_seen.isoformat() if r.last_seen else None,
                    "network_mode": getattr(r, 'network_mode', None)  # AP/STA-L/STA-T from enhanced discovery
                }
                for r in all_robots
            ],
            "count": len(all_robots)
        }
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "robots": [],
            "count": 0
        }


@app.post("/api/bind")
async def bind_robot_endpoint(data: dict):
    """Bind to a robot for future auto-discovery"""
    try:
        from g1_app.core.robot_discovery import RobotInfo
        
        name = data.get("name")
        serial = data.get("serial_number")
        ip = data.get("ip")  # Optional - discovered via mDNS or connection
        
        if not all([name, serial]):
            return {"success": False, "error": "Missing name or serial number"}
        
        robot = RobotInfo(
            name=name,
            serial_number=serial,
            ip=ip if ip else None,
            last_seen=datetime.now() if ip else None
        )
        
        get_discovery().bind_robot(robot)
        logger.info(f"Bound to robot: {name} (IP: {ip if ip else 'auto-discover'})")
        
        return {
            "success": True,
            "message": f"Bound to {name}. IP will be discovered automatically."
        }
    except Exception as e:
        logger.error(f"Bind failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/unbind")
async def unbind_robot_endpoint(data: dict):
    """Remove robot binding"""
    try:
        name = data.get("name")
        if not name:
            return {"success": False, "error": "Missing robot name"}
        
        get_discovery().unbind_robot(name)
        logger.info(f"Unbound robot: {name}")
        
        return {"success": True, "message": f"Unbound {name}"}
    except Exception as e:
        logger.error(f"Unbind failed: {e}")
        return {"success": False, "error": str(e)}


@app.get("/")
async def get_index():
    """Serve the main HTML page"""
    html_file = Path(__file__).parent / "index.html"
    if html_file.exists():
        content = html_file.read_text(encoding='utf-8')
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    else:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors"""
    return Response(content="", media_type="image/x-icon")


# ===== ROBOT MANAGEMENT ENDPOINTS =====

@app.get("/api/robots")
async def get_robots():
    """Get list of all saved robots"""
    robots = load_robots()
    return {"robots": robots}


@app.post("/api/add_robot")
async def add_robot(request: Request):
    """Add a new robot to the configuration"""
    try:
        data = await request.json()
        nickname = data.get('nickname', '').strip()
        mac = data.get('mac', '').strip()
        serial_number = data.get('serial_number', '').strip()

        if not nickname or not mac or not serial_number:
            return {"success": False, "error": "Missing required fields"}

        # Validate MAC format
        if not re.match(r'^([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2})$', mac):
            return {"success": False, "error": "Invalid MAC address format"}

        robots = load_robots()
        
        # Check for duplicates
        if any(r['mac'].lower() == mac.lower() for r in robots):
            return {"success": False, "error": "Robot with this MAC already exists"}

        # Create new robot entry
        robot_id = generate_robot_id(nickname)
        new_robot = {
            'id': robot_id,
            'nickname': nickname,
            'mac': mac.lower(),
            'serial_number': serial_number
        }
        
        robots.append(new_robot)
        save_robots(robots)
        
        logger.info(f"✅ Added new robot: {nickname} ({mac})")
        return {"success": True, "robot": new_robot}
    except Exception as e:
        logger.error(f"Failed to add robot: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/wifi/current")
async def get_current_wifi():
    """Get current WiFi SSID"""
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.split('\n'):
                if line.startswith('yes:'):
                    ssid = line.split(':')[1]
                    is_ap = 'G1_' in ssid or ssid == 'G1_6937'
                    logger.info(f"Current WiFi: {ssid} (AP mode: {is_ap})")
                    return {"ssid": ssid, "is_ap_mode": is_ap}
        
        elif platform.system() == "Windows":
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.split('\n'):
                if 'SSID' in line and 'BSSID' not in line:
                    ssid = line.split(':')[1].strip()
                    is_ap = 'G1_' in ssid
                    logger.info(f"Current WiFi: {ssid} (AP mode: {is_ap})")
                    return {"ssid": ssid, "is_ap_mode": is_ap}
        
        logger.warning("Could not detect WiFi SSID")
        return {"ssid": None, "is_ap_mode": False}
        
    except Exception as e:
        logger.error(f"Failed to get WiFi SSID: {e}")
        return {"ssid": None, "is_ap_mode": False, "error": str(e)}


@app.get("/api/robot/status")
async def get_robot_status():
    """Get current robot connection status"""
    global robot
    
    if not robot or not robot.connected:
        return {
            "connected": False,
            "robot": None,
            "state": None
        }
    
    try:
        state = robot.current_state
        allowed = robot.state_machine.get_allowed_transitions()
        
        return {
            "connected": True,
            "robot": {
                "ip": robot.robot_ip,
                "serial_number": robot.serial_number,
                "mac": getattr(robot, 'robot_mac', None)
            },
            "state": {
                "fsm_state": state.fsm_state.name,
                "fsm_state_value": state.fsm_state.value,
                "fsm_mode": state.fsm_mode,
                "led_color": state.led_color.value,
                "allowed_transitions": [s.name for s in allowed]
            }
        }
    except Exception as e:
        logger.error(f"Error getting robot status: {e}")
        return {
            "connected": robot.connected,
            "robot": {
                "ip": robot.robot_ip if robot else None,
                "serial_number": robot.serial_number if robot else None
            },
            "state": None,
            "error": str(e)
        }


@app.post("/api/connect")
async def connect_robot(mac: str, serial_number: str, mode: str = "auto"):
    """Connect to robot
    
    Args:
        mac: Robot MAC address
        serial_number: Robot serial number  
        mode: Connection mode - 'auto', 'sta', or 'ap'
    """
    global robot
    
    try:
        # Prevent concurrent connection attempts
        if connect_lock.locked():
            return {"success": False, "error": "Connection already in progress. Try again."}

        # If already connected to the same robot, return current state
        if robot and robot.connected and robot.serial_number == serial_number:
            logger.info(f"Already connected to {serial_number}, returning current state")
            state = robot.current_state
            allowed = robot.state_machine.get_allowed_transitions()
            
            # Pause discovery while connected (keep cached robots)
            discovery = get_discovery()
            await discovery.stop(clear=False)

            return {
                "success": True,
                "robot": {
                    "mac": mac,
                    "serial_number": serial_number,
                    "ip": robot.robot_ip
                },
                "state": {
                    "fsm_state": state.fsm_state.name,
                    "fsm_state_value": state.fsm_state.value,
                    "led_color": state.led_color.value,
                    "allowed_transitions": [s.name for s in allowed]
                }
            }
        
        # Enforce single-app connection: if connected to another robot, refuse
        if robot and robot.connected:
            return {"success": False, "error": "Robot already connected. Disconnect first."}
        
        async with connect_lock:
            # Determine IP based on mode
            if mode == "ap":
                # AP mode: use fixed IP
                robot_ip = "192.168.12.1"
                logger.info(f"AP mode connection to {robot_ip}")
                
            else:
                # STA mode or auto: Discover IP from MAC address
                logger.info(f"Discovering robot IP for MAC {mac}...")
                from g1_app.utils.robot_discovery import discover_robot
                discovered = discover_robot(target_mac=mac, verify_with_ping=False)
                
                if not discovered:
                    logger.error(f"Robot with MAC {mac} not found on network")
                    return {
                        "success": False,
                        "error": f"Robot not found on network",
                        "suggestions": [
                            "Check if robot is powered on",
                            "Ensure robot is on same WiFi network",
                            "Try AP mode: Connect to robot's WiFi 'G1_xxxx'"
                        ]
                    }
                
                robot_ip = discovered['ip']
                logger.info(f"Discovered robot at {robot_ip} (SN: {serial_number}, online={discovered.get('online')})")
            
            # Check if robot is reachable
            import subprocess
            import platform
            param = '-n' if platform.system().lower() == "windows" else '-c'
            result = subprocess.run(['ping', param, '1', robot_ip], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                logger.error(f"Robot at {robot_ip} is not reachable on network")
                return {
                    "success": False,
                    "error": f"Robot at {robot_ip} is not reachable",
                    "suggestions": [
                        "Check robot is powered on",
                        "Verify network connection",
                        "Try AP mode if on different network"
                    ]
                }
            
            try:
                robot = RobotController(robot_ip, serial_number)
                robot.robot_mac = mac  # Store MAC address for status API
                await robot.connect()
                
                # Initialize subscriptions for video, state updates, battery, etc.
                await robot.initialize_subscriptions(
                    include_state=True,
                    include_battery=True,
                    include_video=True,
                    include_lidar=True,
                    include_lowstate=False,  # Don't need low-level motor state
                    include_slam=False,      # Don't need SLAM data
                    include_debug=False
                )
                print("DEBUG: Subscriptions initialized", flush=True)
                logger.info("✅ Subscriptions initialized")
                
                # Broadcast initial state to all connected WebSocket clients
                # (on_state_change only fires when state CHANGES, so we need this for first connection)
                print("DEBUG: About to get initial state", flush=True)
                initial_state = robot.current_state
                print(f"DEBUG: Got initial state: {initial_state}", flush=True)
                on_state_change(initial_state)
                print("DEBUG: Called on_state_change", flush=True)
                logger.info("📤 Broadcasted initial state to WebSocket clients")
                
            except Exception as e:
                logger.error(f"Failed to connect to robot: {e}")
                import traceback
                traceback.print_exc()
                robot = None
                return {
                    "success": False,
                    "error": f"Connection failed: {str(e)}",
                    "suggestions": ["Check robot is in correct mode", "Try restarting robot"]
                }
        
        # Get initial state
        state = robot.current_state
        
        # CRITICAL: Get allowed transitions for the initial state
        allowed = robot.state_machine.get_allowed_transitions()
        
        # Pause discovery while connected (keep cached robots)
        discovery = get_discovery()
        await discovery.stop(clear=False)

        return {
            "success": True,
            "robot": {
                "mac": mac,
                "serial_number": serial_number,
                "ip": robot_ip,
                "mode": mode
            },
            "state": {
                "fsm_state": state.fsm_state.name,
                "fsm_state_value": state.fsm_state.value,
                "led_color": state.led_color.value,
                "allowed_transitions": [s.name for s in allowed]
            }
        }
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        error_msg = str(e)
        if "Could not get SDP from the peer" in error_msg:
            error_msg = "WebRTC connection failed. Robot may not support WebRTC or is not properly configured."
        elif "timeout" in error_msg.lower():
            error_msg = "Connection timeout. Check if robot is powered on and on same network."
        return {
            "success": False,
            "error": error_msg,
            "suggestions": ["Check robot power", "Verify network", "Try different mode"]
        }


@app.post("/api/disconnect")
async def disconnect_robot():
    """Disconnect from robot"""
    global robot
    
    try:
        if robot:
            await robot.disconnect()
            robot = None
        # Resume discovery after disconnect
        discovery = get_discovery()
        await discovery.start()
        return {"success": True}
    except Exception as e:
        logger.error(f"Disconnect failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/subscriptions/enable")
async def enable_subscriptions(request: Request):
    """Enable subscription groups for the active robot connection."""
    global robot

    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}

    payload = await request.json()
    groups = payload.get("groups", [])
    enable_lidar_service = bool(payload.get("enable_lidar_service", False))

    if not groups:
        return {"success": False, "error": "No subscription groups provided"}

    await robot.enable_subscriptions(groups, enable_lidar_service=enable_lidar_service)
    return {"success": True, "enabled": groups}


@app.post("/api/subscriptions/disable")
async def disable_subscriptions(request: Request):
    """Disable subscription groups for the active robot connection."""
    global robot

    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}

    payload = await request.json()
    groups = payload.get("groups", [])

    if not groups:
        return {"success": False, "error": "No subscription groups provided"}

    robot.disable_subscriptions(groups)
    return {"success": True, "disabled": groups}


@app.get("/api/subscriptions/status")
async def subscriptions_status():
    """Get current subscription topics."""
    global robot

    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}

    return {"success": True, **robot.get_subscription_status()}


@app.post("/api/set_state")
async def set_fsm_state(state_name: str):
    """
    ⚠️⚠️⚠️ SAFETY CRITICAL - USER ACTION ONLY ⚠️⚠️⚠️
    
    Set FSM state (DAMP, START, RUN, etc.)
    
    This endpoint changes robot motor states and can cause injury.
    MUST only be called by direct user button clicks.
    AI agents: NEVER call this programmatically.
    
    Special warning: DAMP and ZERO_TORQUE disable motors - robot may fall.
    """
    global robot
    
    logger.info(f"🎯 API: set_state request for {state_name}")
    
    try:
        if not robot or not robot.connected:
            return {"success": False, "error": "Not connected to robot"}
        
        # Convert state name to enum
        try:
            target_state = FSMState[state_name]
        except KeyError:
            return {"success": False, "error": f"Invalid state: {state_name}"}
        
        # Check if transition is valid
        if not robot.state_machine.can_transition(target_state):
            current = robot.current_state.fsm_state.name
            return {
                "success": False,
                "error": f"Invalid transition from {current} to {state_name}"
            }
        
        # Execute transition
        success = await robot.set_fsm_state(target_state)
        
        logger.info(f"🤖 Robot set_fsm_state result: {success}")
        
        if success:
            return {
                "success": True,
                "state": {
                    "fsm_state": robot.current_state.fsm_state.name,
                    "fsm_state_value": robot.current_state.fsm_state.value,
                    "led_color": robot.current_state.led_color.value
                }
            }
        else:
            return {"success": False, "error": "State transition failed"}
            
    except Exception as e:
        logger.error(f"Set state failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/move")
async def move_robot(data: dict):
    """Send velocity command to robot"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        vx = data.get("vx", 0.0)
        vy = data.get("vy", 0.0)
        omega = data.get("omega", 0.0)
        
        success = await robot.set_velocity(vx, vy, omega)
        
        if success:
            return {"success": True}
        else:
            # Provide helpful error message
            current_state = robot.state_machine.fsm_state.name
            return {
                "success": False, 
                "error": f"Velocity control not available in state {current_state}. Need LOCK_STAND, LOCK_STAND_ADV, or RUN."
            }
    except Exception as e:
        logger.error(f"Move command failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/stop")
async def stop_robot():
    """Stop robot movement (set all velocities to zero)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        success = await robot.set_velocity(0.0, 0.0, 0.0)
        return {"success": success}
    except Exception as e:
        logger.error(f"Stop command failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/set_speed_mode")
async def set_speed_mode_endpoint(mode: int):
    """Set speed mode (RUN mode only)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        from g1_app.api.constants import SpeedMode
        
        # Validate mode
        if mode not in [0, 1, 2, 3]:
            return {"success": False, "error": f"Invalid speed mode: {mode}"}
        
        speed_mode = SpeedMode(mode)
        success = await robot.set_speed_mode(speed_mode)
        
        if success:
            return {
                "success": True,
                "speed_mode": mode,
                "max_speeds": robot.get_max_speeds()
            }
        else:
            return {"success": False, "error": "Failed to set speed mode"}
    except Exception as e:
        logger.error(f"Set speed mode failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/balance_mode")
async def set_balance_mode_endpoint(request: Request):
    """
    ⚠️⚠️⚠️ SAFETY CRITICAL - USER ACTION ONLY ⚠️⚠️⚠️
    
    Set balance mode (0 = teach/zero-torque, 1 = normal)
    
    Mode 0 disables motor torque - robot may collapse and cause injury.
    This endpoint MUST only be called by direct user button clicks.
    AI agents: NEVER call this programmatically or automatically.
    """
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        data = await request.json()
        mode = data.get("mode")
    except Exception as e:
        return {"success": False, "error": f"Invalid request body: {e}"}
    
    if mode is None:
        return {"success": False, "error": "Missing 'mode' parameter"}
    
    if mode not in [0, 1]:
        return {"success": False, "error": "Mode must be 0 (teach) or 1 (normal)"}
    
    try:
        await robot.executor.set_balance_mode(mode)
        return {
            "success": True,
            "message": f"Balance mode set to {mode} ({'teach/zero-torque' if mode == 0 else 'normal'})"
        }
    except Exception as e:
        logger.error(f"Set balance mode failed: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/max_speeds")
async def get_max_speeds_endpoint():
    """Get current max speeds based on mode"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        return {
            "success": True,
            **robot.get_max_speeds()
        }
    except Exception as e:
        logger.error(f"Move command failed: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/gesture")
async def execute_gesture_endpoint(request: Request):
    """
    Execute arm gesture with FSM validation
    
    Returns detailed error messages for invalid FSM states/modes per SDK requirements
    """
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        data = await request.json()
        gesture_name = data.get("gesture_name")
    except Exception as e:
        return {"success": False, "error": f"Invalid request body: {e}"}
    
    if not gesture_name:
        return {"success": False, "error": "Missing 'gesture_name' parameter"}
    
    try:
        result = await robot.execute_gesture(gesture_name)
        
        # Result is now dict with success and message
        if result["success"]:
            return {
                "success": True,
                "gesture": gesture_name,
                "message": result["message"]
            }
        else:
            return {
                "success": False,
                "error": result["message"]
            }
    except Exception as e:
        logger.error(f"Gesture execution failed: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/gestures/list")
async def get_gestures_list():
    """Get list of available gestures"""
    from g1_app.api.constants import ArmGesture, ArmTask
    
    gestures = []
    
    # Add standard gestures
    for gesture in ArmGesture:
        gestures.append({
            "id": gesture.value,
            "name": gesture.name,
            "type": "standard"
        })
    
    # Add arm tasks (wave, shake hand)
    for task in ArmTask:
        gestures.append({
            "id": task.value,
            "name": task.name,
            "type": "task"
        })
    
    return {
        "success": True,
        "gestures": gestures
    }


@app.post("/api/custom_action/execute")
async def execute_custom_action_endpoint(request: Request):
    """Execute custom teach mode recording"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Command executor not initialized"}
    
    try:
        data = await request.json()
        action_name = data.get("action_name")
    except Exception as e:
        return {"success": False, "error": f"Invalid request body: {e}"}
    
    if not action_name:
        return {"success": False, "error": "Missing 'action_name' parameter"}
    
    try:
        result = await robot.executor.execute_custom_action(action_name)
        logger.info(f"Execute action result: {result}")
        return {
            "success": True,
            "action": action_name,
            "message": f"Playing action: {action_name}",
            "data": result
        }
    except Exception as e:
        logger.error(f"Custom action execution failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/custom_action/stop")
async def stop_custom_action_endpoint():
    """Stop currently playing custom action"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.stop_custom_action()
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            return {
                "success": False,
                "error": result["message"]
            }
    except Exception as e:
        logger.error(f"Stop custom action failed: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/custom_action/list")
async def list_custom_actions_endpoint():
    """Query saved custom teaching actions from robot"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        # Import UDP client
        from g1_app.core.udp_commands import UDPClient
        
        # Get robot IP
        robot_ip = robot.robot_ip
        logger.info(f"🔍 Querying actions from robot at {robot_ip}")
        
        # Query actions via UDP
        client = UDPClient(robot_ip)
        await client.connect()
        actions = await client.query_actions()
        await client.disconnect()
        
        logger.info(f"✅ Query returned {len(actions)} actions")
        
        return {
            "success": True,
            "count": len(actions),
            "actions": [
                {
                    "encrypted_name": action['encrypted_name'].hex(),
                    "timestamp": action['timestamp'],
                    "encrypted_metadata": action['encrypted_metadata'].hex(),
                    "checksum": action['checksum'].hex()
                }
                for action in actions
            ]
        }
    except Exception as e:
        logger.error(f"List actions failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


# ============================================================================
# Teach Mode Endpoints
# ============================================================================

def _generate_action_timestamp() -> str:
    """Generate action name like YYYY-MM-DD_HH:MM:SS (matches phone logs)."""
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

async def _teach_keepalive_loop():
    """Send keepalive packets during teach-mode recording."""
    global teach_recording_active, robot
    while teach_recording_active:
        try:
            if robot and robot.connected and robot.executor:
                await robot.executor.keepalive_teach_recording()
        except Exception as e:
            logger.warning(f"Teach recording keepalive failed: {e}")
        await asyncio.sleep(1.0)


async def _teach_recording_timeout():
    """Auto-stop teach recording after max duration."""
    global teach_recording_active, teach_recording_timeout_task
    await asyncio.sleep(TEACH_RECORDING_MAX_SECONDS)
    if teach_recording_active:
        try:
            await stop_teach_recording()
        except Exception as e:
            logger.warning(f"Teach recording auto-stop failed: {e}")
    teach_recording_timeout_task = None


@app.post("/api/teach/record/start")
async def start_teach_recording(request: Request):
    """Start teach-mode recording using API 7110 with keepalive."""
    global robot, teach_recording_task, teach_recording_timeout_task, teach_recording_active, teach_recording_name

    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}

    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}

    if teach_recording_active:
        return {"success": False, "error": "Recording already in progress"}

    try:
        data = await request.json()
        action_name = data.get("action_name", "").strip()
        if not action_name:
            action_name = _generate_action_timestamp()

        result = await robot.executor.start_teach_recording(action_name)
        teach_recording_active = True
        teach_recording_name = action_name
        teach_recording_task = asyncio.create_task(_teach_keepalive_loop())
        teach_recording_timeout_task = asyncio.create_task(_teach_recording_timeout())

        return {"success": True, "action_name": action_name, "data": result}
    except Exception as e:
        logger.error(f"Teach record start failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/record/stop")
async def stop_teach_recording():
    """Stop teach-mode recording (API 7110) and stop keepalive."""
    global robot, teach_recording_task, teach_recording_timeout_task, teach_recording_active, teach_recording_name

    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}

    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}

    try:
        result = await robot.executor.stop_teach_recording()

        teach_recording_active = False
        if teach_recording_task:
            teach_recording_task.cancel()
            teach_recording_task = None

        if teach_recording_timeout_task:
            teach_recording_timeout_task.cancel()
            teach_recording_timeout_task = None

        return {"success": True, "action_name": teach_recording_name, "data": result}
    except Exception as e:
        logger.error(f"Teach record stop failed: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/teach/actions")
async def get_custom_actions():
    """Get list of custom actions from robot (API 7107)"""
    global robot

    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}

    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}

    try:
        result = await robot.executor.get_custom_action_list()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Get action list failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/rename")
async def rename_teach_action(request: Request):
    """Rename a taught action (API 7109)."""
    global robot

    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}

    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}

    try:
        data = await request.json()
        old_name = data.get("old_name", "").strip()
        new_name = data.get("new_name", "").strip()

        if not old_name or not new_name:
            return {"success": False, "error": "old_name and new_name required"}

        result = await robot.executor.rename_custom_action(old_name, new_name)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Teach rename failed: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/teach/play")
async def play_teach_action(request: Request):
    """Play a custom action (API 7108)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        data = await request.json()
        action_name = data.get("action_name", "").strip()
        
        if not action_name:
            return {"success": False, "error": "action_name required"}
        
        result = await robot.executor.execute_custom_action(action_name)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Play action failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/stop")
async def stop_teach_action():
    """Stop current custom action playback (API 7113)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        result = await robot.executor.stop_custom_action()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Stop action failed: {e}")
        return {"success": False, "error": str(e)}


# ========================================================================
# ARM TEACHING ENDPOINTS (Coordinate-based motion control)
# ========================================================================


# Teach mode page route
@app.get("/teach", response_class=HTMLResponse)
async def teach_mode_page():
    """Serve the teach mode page"""
    try:
        html_path = os.path.join(os.path.dirname(__file__), "teach_mode.html")
        with open(html_path, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load teach mode page: {e}")
        return "<h1>Error loading teach mode page</h1>"


# Point cloud viewer page route
@app.get("/pointcloud", response_class=HTMLResponse)
async def pointcloud_viewer_page():
    """Serve the SLAM point cloud viewer page"""
    try:
        html_path = os.path.join(os.path.dirname(__file__), "pointcloud.html")
        with open(html_path, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load point cloud viewer page: {e}")
        return "<h1>Error loading point cloud viewer</h1>"


# Local storage for custom action favorites (persist across sessions)
CUSTOM_ACTIONS_FILE = "/tmp/g1_custom_actions.json"

def load_custom_actions():
    """Load saved custom action names from file"""
    try:
        if os.path.exists(CUSTOM_ACTIONS_FILE):
            with open(CUSTOM_ACTIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load custom actions: {e}")
    return []

def save_custom_actions(actions):
    """Save custom action names to file"""
    try:
        with open(CUSTOM_ACTIONS_FILE, 'w') as f:
            json.dump(actions, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save custom actions: {e}")
        return False


@app.get("/api/custom_action/list")
async def get_custom_actions_list():
    """Get list of saved custom action names (favorites)"""
    actions = load_custom_actions()
    return {
        "success": True,
        "actions": actions
    }


@app.get("/api/custom_action/robot_list")
async def get_robot_action_list():
    """Get list of all actions from robot (including taught actions)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        response_future = asyncio.get_event_loop().create_future()

        def _handle_response(message):
            try:
                if not isinstance(message, dict):
                    return
                if message.get("type") != "res":
                    return
                data = message.get("data", {})
                header = data.get("header", {})
                identity = header.get("identity", {})
                if identity.get("api_id") != 7107:
                    return
                if not response_future.done():
                    response_future.set_result(message)
            except Exception:
                pass

        robot.conn.datachannel.pub_sub.subscribe("rt/api/arm/response", _handle_response)

        payload = {
            "api_id": 7107,
            "parameter": {}
        }

        await robot.conn.datachannel.pub_sub.publish_request_new("rt/api/arm/request", payload)

        response = await asyncio.wait_for(response_future, timeout=5)
        raw_data = response.get("data", {}).get("data")

        if not raw_data:
            return {"success": False, "error": "Missing action list data"}

        try:
            parsed = json.loads(raw_data)
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
        except Exception as exc:
            return {"success": False, "error": f"Failed to parse action list: {exc}"}

        gestures = parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else []
        custom_actions = parsed[1] if isinstance(parsed, list) and len(parsed) > 1 else []

        return {
            "success": True,
            "gestures": gestures,
            "custom_actions": custom_actions
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "Timed out waiting for robot response"}
    except Exception as e:
        logger.error(f"Failed to get robot action list: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/custom_action/add")
async def add_custom_action(action_name: str):
    """Add custom action to favorites list"""
    actions = load_custom_actions()
    
    if action_name not in actions:
        actions.append(action_name)
        if save_custom_actions(actions):
            return {
                "success": True,
                "message": f"Added '{action_name}' to favorites"
            }
    
    return {
        "success": False,
        "error": "Action already exists"
    }


@app.post("/api/custom_action/remove")
async def remove_custom_action(action_name: str):
    """Remove custom action from favorites list"""
    actions = load_custom_actions()
    
    if action_name in actions:
        actions.remove(action_name)
        if save_custom_actions(actions):
            return {
                "success": True,
                "message": f"Removed '{action_name}' from favorites"
            }
    
    return {
        "success": False,
        "error": "Action not found"
    }


@app.post("/api/custom_action/rename")
async def rename_custom_action(old_name: str, new_name: str):
    """Rename custom action in favorites list"""
    actions = load_custom_actions()
    
    if old_name in actions:
        index = actions.index(old_name)
        actions[index] = new_name
        if save_custom_actions(actions):
            return {
                "success": True,
                "message": f"Renamed '{old_name}' to '{new_name}'"
            }
    
    return {
        "success": False,
        "error": "Action not found"
    }


@app.get("/api/gestures/list")
async def get_gestures_list():
    """Get list of available gestures"""
    from g1_app.api.constants import ArmGesture, ArmTask
    
    try:
        # Return both simple tasks and complex gestures
        return {
            "success": True,
            "simple_tasks": [
                {"name": "WAVE_HAND", "value": ArmTask.WAVE_HAND.value, "display": "👋 Wave Hand"},
                {"name": "WAVE_HAND_TURN", "value": ArmTask.WAVE_HAND_TURN.value, "display": "👋 Wave + Turn"},
                {"name": "SHAKE_HAND_STAGE_1", "value": ArmTask.SHAKE_HAND_STAGE_1.value, "display": "🤝 Shake Hand (1)"},
                {"name": "SHAKE_HAND_STAGE_2", "value": ArmTask.SHAKE_HAND_STAGE_2.value, "display": "🤝 Shake Hand (2)"},
            ],
            "gestures": [
                {"name": "TWO_HAND_KISS", "value": ArmGesture.TWO_HAND_KISS.value, "display": "😘 Two Hand Kiss"},
                {"name": "HANDS_UP", "value": ArmGesture.HANDS_UP.value, "display": "🙌 Hands Up"},
                {"name": "CLAP", "value": ArmGesture.CLAP.value, "display": "👏 Clap"},
                {"name": "HIGH_FIVE", "value": ArmGesture.HIGH_FIVE.value, "display": "✋ High Five"},
                {"name": "HUG", "value": ArmGesture.HUG.value, "display": "🤗 Hug"},
                {"name": "HEART", "value": ArmGesture.HEART.value, "display": "❤️ Heart (2 hands)"},
                {"name": "RIGHT_HEART", "value": ArmGesture.RIGHT_HEART.value, "display": "💝 Right Heart"},
                {"name": "REJECT", "value": ArmGesture.REJECT.value, "display": "🚫 Reject"},
                {"name": "RIGHT_HAND_UP", "value": ArmGesture.RIGHT_HAND_UP.value, "display": "✋ Right Hand Up"},
                {"name": "X_RAY", "value": ArmGesture.X_RAY.value, "display": "🔍 X-Ray"},
                {"name": "FACE_WAVE", "value": ArmGesture.FACE_WAVE.value, "display": "👋 Face Wave"},
                {"name": "HIGH_WAVE", "value": ArmGesture.HIGH_WAVE.value, "display": "👋 High Wave"},
                {"name": "SHAKE_HAND", "value": ArmGesture.SHAKE_HAND.value, "display": "🤝 Shake Hand"},
                {"name": "RELEASE_ARM", "value": ArmGesture.RELEASE_ARM.value, "display": "🔓 Release Arms"},
            ]
        }
    except Exception as e:
        logger.error(f"Get gestures list failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/arm/read_pose")
async def read_current_pose():
    """Read current arm joint positions"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}
    
    try:
        # Read current arm positions
        left_data = await robot.request_arm_state('left')
        right_data = await robot.request_arm_state('right')
        
        if not left_data or not right_data:
            return {"success": False, "error": "Failed to read arm state from robot"}
        
        return {
            "success": True,
            "left_arm": left_data['joints'],
            "right_arm": right_data['joints']
        }
    except Exception as e:
        logger.error(f"Read pose failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/debug/transitions")
async def debug_transitions():
    """Debug endpoint to check transitions"""
    global robot
    
    if not robot or not robot.connected:
        return {"error": "Not connected"}
    
    current = robot.state_machine.fsm_state
    transitions_raw = robot.state_machine.TRANSITIONS.get(current, set())
    allowed = robot.state_machine.get_allowed_transitions()
    
    return {
        "current_state": current.name,
        "current_value": current.value,
        "transitions_from_dict": [s.name for s in sorted(transitions_raw, key=lambda x: x.value)],
        "transitions_from_dict_count": len(transitions_raw),
        "allowed_from_method": [s.name for s in sorted(allowed, key=lambda x: x.value)],
        "allowed_from_method_count": len(allowed)
    }


@app.get("/api/state")
async def get_current_state():
    """Get current robot state"""
    global robot
    
    try:
        if not robot or not robot.connected:
            return {"success": False, "error": "Not connected"}
        
        state = robot.current_state
        allowed = robot.state_machine.get_allowed_transitions()
        
        # Debug logging
        logger.info(f"Current state: {state.fsm_state.name} ({state.fsm_state.value})")
        logger.info(f"Allowed transitions count: {len(allowed)}")
        logger.info(f"Allowed transitions: {[s.name for s in sorted(allowed, key=lambda x: x.value)]}")
        
        return {
            "success": True,
            "state": {
                "fsm_state": state.fsm_state.name,
                "fsm_state_value": state.fsm_state.value,
                "led_color": state.led_color.value,
                "error": state.error,
                "allowed_transitions": [s.name for s in allowed]
            }
        }
    except Exception as e:
        logger.error(f"Get state failed: {e}")
        return {"success": False, "error": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()
            # Echo back for ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# Audio Control Endpoints
# ============================================================================

@app.post("/api/audio/speak")
async def speak_text(data: dict):
    """Text-to-speech"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    text = data.get("text", "")
    speaker_id = data.get("speaker_id", 0)  # 0=Chinese, 1=English
    
    if not text:
        return {"success": False, "error": "No text provided"}
    
    result = await robot.speak(text, speaker_id)
    return result


@app.post("/api/audio/volume")
async def set_volume(data: dict):
    """Set system volume"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    volume = data.get("volume")
    if volume is None or not (0 <= volume <= 100):
        return {"success": False, "error": "Volume must be 0-100"}
    
    result = await robot.set_volume(volume)
    return result


@app.get("/api/audio/volume")
async def get_volume():
    """Get current system volume"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    result = await robot.get_volume()
    return result


@app.post("/api/audio/led")
async def set_led_color(data: dict):
    """Set RGB light strip color"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    r = data.get("r", 0)
    g = data.get("g", 0)
    b = data.get("b", 0)
    
    result = await robot.set_led_color(r, g, b)
    return result


# ============================================================================
# Video Stream Endpoint (via WebRTC)
# ============================================================================

@app.get("/api/video/status")
async def get_video_status():
    """Get video stream status"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    # Check if WebRTC video track is available
    if hasattr(robot.conn, 'video_track') and robot.conn.video_track:
        return {
            "success": True,
            "available": True,
            "message": "Video stream available via WebRTC"
        }
    else:
        return {
            "success": True,
            "available": False,
            "message": "Video stream not yet initialized"
        }

@app.get("/api/video/stream")
async def video_stream():
    """MJPEG video stream from robot camera"""
    from fastapi.responses import StreamingResponse
    import asyncio
    import cv2
    import numpy as np
    
    async def generate_frames():
        """Generate MJPEG frames from WebRTC video"""
        global robot
        
        while True:
            if not robot or not robot.connected:
                # Send placeholder frame when disconnected
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "No video - Robot disconnected", (50, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                _, buffer = cv2.imencode('.jpg', placeholder)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            elif hasattr(robot, 'latest_frame') and robot.latest_frame is not None:
                # Send actual video frame
                frame = robot.latest_frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Waiting for first frame
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Waiting for video...", (150, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                _, buffer = cv2.imencode('.jpg', placeholder)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            await asyncio.sleep(0.033)  # ~30 FPS
    
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


# ============================================================================
# LiDAR Status Endpoint
# ============================================================================

@app.get("/api/status")
async def get_status():
    """Get overall robot status"""
    global robot
    
    try:
        print(f"DEBUG /api/status: robot={robot}, robot.connected={robot.connected if robot else 'N/A'}")
        connected = robot.connected if robot else False
        robot_name = "Unknown"
        fsm_id = 0
        battery = 0
        
        if robot:
            if hasattr(robot, 'robot_name'):
                robot_name = robot.robot_name
            if connected and hasattr(robot, 'state_machine') and robot.state_machine:
                if hasattr(robot.state_machine, 'current_state'):
                    fsm_id = robot.state_machine.current_state.fsm_id
                    battery = robot.state_machine.current_state.battery_percentage
        
        return {
            "connected": connected,
            "robot_name": robot_name,
            "fsm_id": fsm_id,
            "battery": battery
        }
    except Exception as e:
        logger.error(f"Error in /api/status: {e}", exc_info=True)
        return {
            "connected": False,
            "robot_name": "Error",
            "fsm_id": 0,
            "battery": 0
        }

@app.get("/api/lidar/status")
async def get_lidar_status():
    """Get LiDAR status"""
    global robot
    
    try:
        if not robot or not robot.connected:
            return {"success": False, "error": "Not connected"}
        
        topics = robot.get_subscription_status().get("topics", [])
        lidar_topics = [
            "rt/unitree/slam_mapping/points",
            "rt/utlidar/cloud_livox_mid360",
            "rt/utlidar/imu_livox_mid360",
        ]
        subscribed = [topic for topic in lidar_topics if topic in topics]

        return {
            "success": True,
            "subscribed_topics": subscribed,
            "all_topics": lidar_topics,
        }
    except Exception as e:
        logger.error(f"Error in /api/lidar/status: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/lidar/service")
async def set_lidar_service(request: Request):
    """Enable or disable the lidar_driver service (explicit user action only)."""
    global robot

    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}

    payload = await request.json()
    enable = bool(payload.get("enable", False))

    await robot.set_lidar_service(enable)
    return {"success": True, "enable": enable}

@app.get("/api/lidar/pointcloud")
async def get_lidar_pointcloud():
    """Get latest LiDAR point cloud"""
    global robot
    
    try:
        if not robot or not hasattr(robot, 'latest_lidar_points'):
            return {"success": True, "points": [], "count": 0}
        
        points = robot.latest_lidar_points if robot.latest_lidar_points else []
        
        # Limit response size - only send every Nth point if too many
        max_points = 5000
        if len(points) > max_points:
            step = len(points) // max_points
            points = points[::step]
        
        return {
            "success": True,
            "points": points,
            "count": len(points)
        }
    except Exception as e:
        logger.error(f"Error in /api/lidar/pointcloud: {e}", exc_info=True)
        return {"success": True, "points": [], "count": 0}


@app.post("/api/slam/start")
async def slam_start():
    """Start SLAM mapping to enable LiDAR"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.slam_start_mapping()
        return {"success": True, "command": result}
    except Exception as e:
        logger.error(f"Failed to start SLAM: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/slam/stop")
async def slam_stop():
    """Stop SLAM mapping"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.slam_stop_mapping()
        return {"success": True, "command": result}
    except Exception as e:
        logger.error(f"Failed to stop SLAM: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/slam/close")
async def slam_close():
    """Close SLAM and disable LiDAR"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.slam_close()
        return {"success": True, "command": result}
    except Exception as e:
        logger.error(f"Failed to close SLAM: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/slam/trajectory")
async def get_slam_trajectory():
    """Get current SLAM trajectory for live 3D visualization"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected", "points": []}
    
    try:
        trajectory = getattr(robot, 'slam_trajectory', [])
        return {
            "success": True,
            "points": trajectory,
            "count": len(trajectory),
            "active": getattr(robot, 'slam_active', False)
        }
    except Exception as e:
        logger.error(f"Error getting trajectory: {e}")
        return {"success": False, "error": str(e), "points": []}

@app.get("/api/slam/download_map")
async def download_slam_map():
    """Download the PCD map file generated by SLAM
    
    The map is saved on the robot at /home/unitree/temp_map.pcd
    Try to retrieve it via HTTP if available.
    """
    from fastapi.responses import JSONResponse, Response
    global robot
    
    if not robot or not robot.connected:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Not connected"}
        )
    
    robot_ip = robot.robot_ip
    map_filename = "temp_map.pcd"
    
    # Try common HTTP endpoints where the robot might serve files
    import httpx
    possible_urls = [
        f"http://{robot_ip}:8080/files/{map_filename}",
        f"http://{robot_ip}:8000/{map_filename}",
        f"http://{robot_ip}:9000/download/{map_filename}",
        f"http://{robot_ip}/slam/{map_filename}",
    ]
    
    for url in possible_urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200 and len(response.content) > 100:
                    return Response(
                        content=response.content,
                        media_type="application/octet-stream",
                        headers={"Content-Disposition": f"attachment; filename={map_filename}"}
                    )
        except Exception as e:
            logger.debug(f"Failed to download from {url}: {e}")
            continue
    
    # File not accessible via HTTP
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Map file not accessible via HTTP",
            "info": {
                "robot_ip": robot_ip,
                "map_path": f"/home/unitree/{map_filename}",
                "suggestion": "G1 Air may not expose file download endpoints. Use SLAM point cloud data instead."
            }
        }
    )


# ============================================================================
# SLAM Map Management and Navigation Endpoints
# ============================================================================

@app.get("/api/slam/maps")
async def get_saved_maps():
    """Get list of saved SLAM maps on the robot"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected", "maps": []}
    
    try:
        logger.info("Querying robot for saved SLAM maps...")
        
        maps = []
        
        # Try to detect maps by probing common names
        # These are typical map names used by Unitree robots
        common_map_names = [
            "test1", "test2", "test3", "test4", "test5",
            "map1", "map2", "room1", "room2",
            "recorded_map", "exported_map", "main", "default",
            "front_room", "kitchen", "bedroom", "garage",
            "floor1", "floor2"
        ]
        
        # Try to get list from SLAM service or fallback to common names
        detected_maps = []
        
        # Try SLAM query (may not be supported on all robots)
        try:
            # Send a simple query to SLAM service to list available maps
            # This will be supported on robots with SLAM service enabled
            query_payload = {
                "api_id": 1950,  # Custom map list query
            }
            
            await asyncio.wait_for(
                robot.executor.datachannel.pub_sub.publish_request_new(
                    f"rt/api/slam/request",
                    query_payload
                ),
                timeout=3.0
            )
            
            logger.info("Sent map list query to SLAM service")
        except Exception as e:
            logger.debug(f"SLAM service query not available: {e}")
        
        # For now, return common map names that can be probed
        # The robot will confirm if each map exists when user tries to load it
        for map_name in common_map_names[:10]:  # Limit to first 10
            detected_maps.append({
                "name": f"{map_name}.pcd",
                "path": f"/home/unitree/{map_name}.pcd",
                "loadable": True
            })
        
        # If we found maps, return them
        if detected_maps:
            logger.info(f"📍 Probing found {len(detected_maps)} potential maps")
            return {
                "success": True,
                "maps": detected_maps,
                "count": len(detected_maps),
                "note": "Showing detected map slots. Verify by loading."
            }
        
        # No maps found
        return {
            "success": True,
            "maps": [],
            "count": 0,
            "note": "No maps detected. Start SLAM mapping to create maps."
        }
        
    except Exception as e:
        logger.error(f"Error getting maps list: {e}")
        return {"success": False, "error": str(e), "maps": []}


@app.post("/api/slam/load_map")
async def load_map(request: Request):
    """Load a saved SLAM map and initialize robot pose for navigation
    
    Request body:
    {
        "map_name": "test1.pcd",  # Name of map file (with or without .pcd)
        "x": 0.0,                 # Optional: initial robot position
        "y": 0.0,
        "z": 0.0
    }
    """
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        data = await request.json()
        map_name = data.get("map_name", "test1.pcd")
        x = float(data.get("x", 0.0))
        y = float(data.get("y", 0.0))
        z = float(data.get("z", 0.0))
        
        # Send load map command
        result = await robot.executor.slam_load_map(map_name, x, y, z)
        
        # Update robot state
        robot.navigation_active = True
        robot.loaded_map = map_name
        robot.navigation_goal = None
        
        logger.info(f"🗺️  Map '{map_name}' loaded for navigation")
        
        return {
            "success": True,
            "command": result,
            "map": map_name,
            "initial_pose": {"x": x, "y": y, "z": z},
            "status": "ready_for_navigation"
        }
    except Exception as e:
        logger.error(f"Error loading map: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/slam/navigate_to")
async def navigate_to_goal(request: Request):
    """Send robot to a specific position in the loaded map
    
    Request body:
    {
        "x": 2.0,      # Target X position (meters)
        "y": 1.5,      # Target Y position (meters)
        "z": 0.0       # Optional: target height
    }
    
    Note: Target must be within 10 meters of current position
    """
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not getattr(robot, 'navigation_active', False):
        return {"success": False, "error": "Navigation not active - load a map first"}
    
    try:
        data = await request.json()
        x = float(data.get("x"))
        y = float(data.get("y"))
        z = float(data.get("z", 0.0))
        
        # Send navigation command
        result = await robot.executor.slam_navigate_to(x, y, z)
        
        # Store goal
        robot.navigation_goal = {"x": x, "y": y, "z": z, "timestamp": datetime.now().isoformat()}
        
        logger.info(f"🎯 Navigation goal set: ({x}, {y}, {z})")
        
        return {
            "success": True,
            "command": result,
            "goal": robot.navigation_goal,
            "status": "navigating"
        }
    except Exception as e:
        logger.error(f"Error sending navigation goal: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/slam/pause_navigation")
async def pause_navigation():
    """Pause active navigation"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.slam_pause_navigation()
        logger.info("⏸️  Navigation paused")
        return {"success": True, "command": result, "status": "paused"}
    except Exception as e:
        logger.error(f"Error pausing navigation: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/slam/resume_navigation")
async def resume_navigation():
    """Resume paused navigation"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.slam_resume_navigation()
        logger.info("▶️  Navigation resumed")
        return {"success": True, "command": result, "status": "resumed"}
    except Exception as e:
        logger.error(f"Error resuming navigation: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/slam/navigation_status")
async def get_navigation_status():
    """Get current navigation status"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    return {
        "success": True,
        "navigation_active": getattr(robot, 'navigation_active', False),
        "loaded_map": getattr(robot, 'loaded_map', None),
        "current_goal": getattr(robot, 'navigation_goal', None),
        "slam_info": {
            "active": getattr(robot, 'slam_active', False),
            "trajectory_points": len(getattr(robot, 'slam_trajectory', [])),
            "latest_pose": robot.slam_trajectory[-1] if getattr(robot, 'slam_trajectory', []) else None
        }
    }


@app.get("/api/slam/current_position")
async def get_current_position():
    """Get current robot position from SLAM relocation odometry
    
    Returns:
    {
        "success": true,
        "position": {
            "x": 1.234,        # Position in meters
            "y": 0.567,
            "z": 0.000,
            "heading": 45.2    # Heading in degrees
        },
        "updates_received": 120,  # Number of position updates
        "has_relocation": true,   # Whether relocation is active
        "timestamp": 1707123456.789
    }
    """
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    position = getattr(robot, 'current_position', {})
    updates = getattr(robot, 'current_position_updates', 0)
    
    return {
        "success": True,
        "position": position,
        "updates_received": updates,
        "has_relocation": updates > 0,
        "timestamp": position.get('timestamp', 0)
    }


# ========================================================================
# ALL Teaching Mode API Endpoints REMOVED - Used Unconfirmed UDP Protocol
# Phone logs show WebRTC JSON protocol only (APIs 7107-7113)
# See /api/teach/* endpoints above for confirmed phone-log-based implementation
# ========================================================================


# ============================================================================
# ARM TEACHING ENDPOINTS (Coordinate-based motion control)
# ============================================================================

@app.post("/api/arm/move")
async def arm_move(request: Request):
    """
    Move arm to specified joint positions
    
    Body:
        {
            "arm": "left" or "right",
            "joints": [7 joint angles in radians],
            "speed": 1.0 (optional, movement speed multiplier)
        }
    """
    global robot, arm_controller
    
    logger.debug("=== API /api/arm/move called ===")
    logger.debug(f"Robot connected: {robot.connected if robot else False}")
    
    if not robot or not robot.connected:
        logger.warning("API call rejected: not connected to robot")
        return {"success": False, "error": "Not connected to robot"}
    
    try:
        data = await request.json()
        logger.debug(f"Request data: {data}")
        
        arm = data.get("arm", "left")
        joints = data.get("joints", [])
        speed = data.get("speed", 1.0)
        
        logger.debug(f"Arm: {arm}, Speed: {speed}")
        logger.debug(f"Joints count: {len(joints)}")
        logger.debug(f"Joints (rad): {joints}")
        logger.debug(f"Joints (deg): {[f'{j*180/3.14159:.1f}°' for j in joints]}")
        
        if len(joints) != 7:
            logger.warning(f"Invalid joint count: {len(joints)}")
            return {"success": False, "error": f"Expected 7 joints, got {len(joints)}"}
        
        # Initialize arm controller if needed
        if arm_controller is None:
            logger.debug("Initializing arm controller...")
            arm_controller = ArmController(robot)
        
        # Calculate duration based on speed
        duration = 2.0 / speed
        logger.debug(f"Movement duration: {duration}s")
        
        # Send command to robot
        logger.debug("Calling arm_controller.move_to_pose()...")
        success = await arm_controller.move_to_pose(arm, joints, duration=duration)
        logger.debug(f"move_to_pose() returned: {success}")
        
        if success:
            logger.info(f"✅ Successfully sent {arm} arm command")
            return {
                "success": True,
                "message": f"Moving {arm} arm to target pose",
                "joints": joints
            }
        else:
            logger.error("❌ Failed to send arm command")
            return {"success": False, "error": "Failed to send arm command"}
            
    except Exception as e:
        logger.error(f"❌ Arm move failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.get("/api/arm/read")
async def arm_read(arm: str = "left"):
    """
    Read current arm joint positions
    
    Args:
        arm: "left" or "right"
        
    Returns:
        {
            "success": true,
            "arm": "left",
            "joints": [7 joint angles in radians]
        }
    """
    global robot, arm_controller
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected to robot"}
    
    try:
        # Initialize arm controller if needed
        if arm_controller is None:
            arm_controller = ArmController(robot)
        
        # Read current pose from robot
        joints = await arm_controller.read_current_pose(arm)
        
        if joints:
            return {
                "success": True,
                "arm": arm,
                "joints": joints
            }
        else:
            return {"success": False, "error": "Failed to read arm pose"}
            
    except Exception as e:
        logger.error(f"Arm read failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/arm/play_sequence")
async def arm_play_sequence(request: Request):
    """
    Play back a sequence of waypoints
    
    Body:
        {
            "waypoints": [
                {"arm": "left", "joints": [7 angles]},
                {"arm": "right", "joints": [7 angles]},
                ...
            ],
            "speed": 1.0 (optional)
        }
    """
    global robot, arm_controller
    
    logger.debug("=== API /api/arm/play_sequence called ===")
    logger.debug(f"Robot connected: {robot.connected if robot else False}")
    
    if not robot or not robot.connected:
        logger.warning("API call rejected: not connected to robot")
        return {"success": False, "error": "Not connected to robot"}
    
    try:
        data = await request.json()
        waypoints = data.get("waypoints", [])
        speed = data.get("speed", 1.0)
        
        logger.debug(f"Waypoint count: {len(waypoints)}")
        logger.debug(f"Speed: {speed}")
        logger.debug(f"Waypoints: {waypoints}")
        
        if not waypoints:
            logger.warning("No waypoints provided")
            return {"success": False, "error": "No waypoints provided"}
        
        # Initialize arm controller if needed
        if arm_controller is None:
            logger.debug("Initializing arm controller...")
            arm_controller = ArmController(robot)
        
        # Play sequence
        logger.info(f"▶️ Starting sequence playback ({len(waypoints)} waypoints)")
        success = await arm_controller.play_sequence(waypoints, speed)
        logger.debug(f"play_sequence() returned: {success}")
        
        if success:
            logger.info(f"✅ Sequence playback completed successfully")
            return {
                "success": True,
                "message": f"Played sequence with {len(waypoints)} waypoints",
                "waypoint_count": len(waypoints)
            }
        else:
            logger.error("❌ Sequence playback failed")
            return {"success": False, "error": "Sequence playback failed"}
            
    except Exception as e:
        logger.error(f"❌ Sequence playback failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.get("/api/arm/presets")
async def arm_presets(arm: str = "left"):
    """
    Get available preset poses for arm
    
    Args:
        arm: "left" or "right"
        
    Returns:
        {
            "success": true,
            "presets": {
                "rest": [7 joint angles],
                "forward_reach": [7 joint angles],
                ...
            }
        }
    """
    global arm_controller
    
    try:
        # Initialize arm controller if needed
        if arm_controller is None:
            arm_controller = ArmController(None)
        
        presets = arm_controller.preset_poses(arm)
        
        return {
            "success": True,
            "arm": arm,
            "presets": presets
        }
        
    except Exception as e:
        logger.error(f"Get presets failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/arm/preset/{preset_name}")
async def arm_go_to_preset(preset_name: str, arm: str = "left", speed: float = 1.0):
    """
    Move arm to a preset pose
    
    Args:
        preset_name: Name of preset (e.g., "rest", "forward_reach", "button_push")
        arm: "left" or "right"
        speed: Movement speed multiplier
    """
    global robot, arm_controller
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected to robot"}
    
    try:
        # Initialize arm controller if needed
        if arm_controller is None:
            arm_controller = ArmController(robot)
        
        duration = 2.0 / speed
        success = await arm_controller.go_to_preset(arm, preset_name, duration)
        
        if success:
            return {
                "success": True,
                "message": f"Moving {arm} arm to '{preset_name}' pose"
            }
        else:
            return {"success": False, "error": f"Unknown preset: {preset_name}"}
            
    except Exception as e:
        logger.error(f"Go to preset failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def main():
    """Run the web server"""
    logger.info("Starting G1 Web UI Server")
    logger.info("Open http://localhost:3000 in your browser")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
