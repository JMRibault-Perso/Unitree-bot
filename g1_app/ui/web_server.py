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
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path for Windows compatibility
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
sys.path.insert(0, '/root/G1/unitree_sdk2')

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import re

from g1_app import RobotController, EventBus, Events, FSMState, LEDColor
from g1_app.utils import setup_app_logging
from g1_app.core.robot_discovery import get_discovery

# Setup logging
setup_app_logging(verbose=True)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="G1 Robot Controller")

# Global robot controller
robot: Optional[RobotController] = None
connect_lock = asyncio.Lock()
connected_clients = []


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
    """Broadcast LiDAR status to all web clients (throttled)"""
    try:
        # Only broadcast metadata, not full point cloud
        asyncio.create_task(manager.broadcast({
            "type": "lidar_active",
            "data": {
                "active": True,
                "height": data.get("height"),
                "width": data.get("width"),
                "point_step": data.get("point_step")
            }
        }))
    except Exception as e:
        logger.error(f"Error in on_lidar_data_received: {e}")


# Subscribe to events
EventBus.subscribe(Events.STATE_CHANGED, on_state_change)
EventBus.subscribe(Events.CONNECTION_CHANGED, on_connection_change)
EventBus.subscribe(Events.BATTERY_UPDATED, on_battery_update)
EventBus.subscribe(Events.SPEECH_RECOGNIZED, on_speech_recognized)
EventBus.subscribe(Events.LIDAR_DATA_RECEIVED, on_lidar_data_received)


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
async def discover_robots_endpoint():
    """Get list of discovered robots on the network"""
    logger.info("🔍 Discovery endpoint called")
    
    try:
        discovery = get_discovery()
        
        # Get all robots (bound + discovered)
        all_robots = await discovery.get_robots()
        bound_robots = discovery.get_bound_robots()
        
        logger.info(f"Found {len(all_robots)} total robots ({len(bound_robots)} bound)")
        
        return {
            "success": True,
            "robots": [
                {
                    "name": r.name,
                    "serial_number": r.serial_number,
                    "ip": r.ip,
                    "is_bound": r.name in [b.name for b in bound_robots],
                    "is_online": r.is_online,
                    "last_seen": r.last_seen.isoformat() if r.last_seen else None
                }
                for r in all_robots
            ],
            "count": len(all_robots),
            "bound_count": len(bound_robots)
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
        content = html_file.read_text()
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


@app.post("/api/connect")
async def connect_robot(ip: str, serial_number: str):
    """Connect to robot"""
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
            
            return {
                "success": True,
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
            logger.info(f"Connecting to robot at {ip} (SN: {serial_number})")
            
            # First check if robot is reachable
            import subprocess
            import platform
            param = '-n' if platform.system().lower() == "windows" else '-c'
            result = subprocess.run(['ping', param, '1', ip], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                logger.error(f"Robot at {ip} is not reachable on network")
                return {"success": False, "error": f"Robot at {ip} is not reachable. Check if robot is powered on and on same network."}
            
            try:
                robot = RobotController(ip, serial_number)
                await robot.connect()
            except Exception as e:
                logger.error(f"Failed to connect to robot: {e}")
                import traceback
                traceback.print_exc()
                robot = None
                return {"success": False, "error": f"Failed to connect: {str(e)}"}
        
        # Get initial state
        state = robot.current_state
        
        # CRITICAL: Get allowed transitions for the initial state
        allowed = robot.state_machine.get_allowed_transitions()
        
        return {
            "success": True,
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
        return {"success": False, "error": error_msg}


@app.post("/api/disconnect")
async def disconnect_robot():
    """Disconnect from robot"""
    global robot
    
    try:
        if robot:
            await robot.disconnect()
            robot = None
        return {"success": True}
    except Exception as e:
        logger.error(f"Disconnect failed: {e}")
        return {"success": False, "error": str(e)}


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
async def set_balance_mode_endpoint(mode: int):
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
        await robot.executor.set_balance_mode(mode)
        return {
            "success": True,
            "message": f"Balance mode set to {mode} (FSM should transition to 501)"
        }
    except Exception as e:
        logger.error(f"Set balance mode failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/start_recording")
async def start_recording_endpoint():
    """EXPERIMENTAL: Start recording teach mode action (API 7109)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        result = await robot.executor.start_record_action()
        logger.info(f"Start recording result: {result}")
        return {
            "success": True,
            "message": "Recording started (experimental API)",
            "data": result
        }
    except Exception as e:
        logger.error(f"Start recording failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/stop_recording")
async def stop_recording_endpoint():
    """EXPERIMENTAL: Stop recording teach mode action (API 7110)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        result = await robot.executor.stop_record_action()
        logger.info(f"Stop recording result: {result}")
        return {
            "success": True,
            "message": "Recording stopped (experimental API)",
            "data": result
        }
    except Exception as e:
        logger.error(f"Stop recording failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/save_recording")
async def save_recording_endpoint(action_name: str):
    """EXPERIMENTAL: Save recorded action with name (API 7111)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        result = await robot.executor.save_recorded_action(action_name)
        logger.info(f"Save recording result: {result}")
        return {
            "success": True,
            "message": f"Recording saved as '{action_name}' (experimental API)",
            "data": result
        }
    except Exception as e:
        logger.error(f"Save recording failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/delete_action")
async def delete_action_endpoint(action_name: str):
    """EXPERIMENTAL: Delete saved action (API 7112)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    try:
        result = await robot.executor.delete_action(action_name)
        logger.info(f"Delete action result: {result}")
        return {
            "success": True,
            "message": f"Action '{action_name}' deleted (experimental API)",
            "data": result
        }
    except Exception as e:
        logger.error(f"Delete action failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/rename_action")
async def rename_action_endpoint(old_name: str, new_name: str):
    """EXPERIMENTAL: Rename saved action (API 7113)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Executor not initialized"}
    
    if not old_name or not new_name:
        return {"success": False, "error": "Action names cannot be empty"}
    
    try:
        result = await robot.executor.rename_action(old_name, new_name)
        logger.info(f"Rename action result: {result}")
        return {
            "success": True,
            "message": f"Action '{old_name}' renamed to '{new_name}' (experimental API)",
            "data": result
        }
    except Exception as e:
        logger.error(f"Rename action failed: {e}")
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
async def execute_gesture_endpoint(gesture_name: str):
    """
    Execute arm gesture with FSM validation
    
    Returns detailed error messages for invalid FSM states/modes per SDK requirements
    """
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
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
async def execute_custom_action_endpoint(action_name: str):
    """Execute custom teach mode recording"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    if not robot.executor:
        return {"success": False, "error": "Command executor not initialized"}
    
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


@app.get("/api/test/hidden_apis")
async def test_hidden_apis():
    """Test hidden APIs 7109-7112 to see if they exist"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    results = {}
    
    # Test API 7107 - GetActionList (documented)
    try:
        result = await robot.get_custom_action_list()
        results["7107_GET_ACTION_LIST"] = {
            "success": result["success"],
            "data": result.get("actions", result.get("message"))
        }
    except Exception as e:
        results["7107_GET_ACTION_LIST"] = {"success": False, "error": str(e)}
    
    # Test API 7109 - START_RECORD_ACTION (hypothesis)
    try:
        response = await robot.send_api_command(7109, {})
        results["7109_START_RECORD"] = {
            "raw_response": response,
            "exists": response.get("error_code") != 3104 if isinstance(response, dict) else True
        }
    except Exception as e:
        results["7109_START_RECORD"] = {"error": str(e)}
    
    # Test API 7110 - STOP_RECORD_ACTION (hypothesis)
    try:
        response = await robot.send_api_command(7110, {})
        results["7110_STOP_RECORD"] = {
            "raw_response": response,
            "exists": response.get("error_code") != 3104 if isinstance(response, dict) else True
        }
    except Exception as e:
        results["7110_STOP_RECORD"] = {"error": str(e)}
    
    # Test API 7111 - SAVE_RECORDED_ACTION (hypothesis)
    try:
        response = await robot.send_api_command(7111, {"action_name": "test_probe"})
        results["7111_SAVE_RECORD"] = {
            "raw_response": response,
            "exists": response.get("error_code") != 3104 if isinstance(response, dict) else True
        }
    except Exception as e:
        results["7111_SAVE_RECORD"] = {"error": str(e)}
    
    # Test API 7112 - DELETE_ACTION (hypothesis)
    try:
        response = await robot.send_api_command(7112, {"action_name": "test_probe"})
        results["7112_DELETE_ACTION"] = {
            "raw_response": response,
            "exists": response.get("error_code") != 3104 if isinstance(response, dict) else True
        }
    except Exception as e:
        results["7112_DELETE_ACTION"] = {"error": str(e)}
    
    return {"success": True, "results": results}


# ============================================================================
# Teach Mode Endpoints
# ============================================================================

@app.post("/api/teach/start_record")
async def start_recording():
    """Start recording arm movements (API 7109)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}
    
    try:
        result = await robot.send_api_command(7109, {})
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Start recording failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/stop_record")
async def stop_recording():
    """Stop recording arm movements (API 7110)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}
    
    try:
        result = await robot.send_api_command(7110, {})
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Stop recording failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/save_action")
async def save_recorded_action(request: Request):
    """Save recorded action with a name (API 7111)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}
    
    try:
        data = await request.json()
        action_name = data.get("action_name", "").strip()
        
        if not action_name:
            return {"success": False, "error": "action_name required"}
        
        # Validate action name
        if not re.match(r'^[a-zA-Z0-9_]+$', action_name):
            return {"success": False, "error": "Invalid action name. Use only letters, numbers, and underscores."}
        
        result = await robot.send_api_command(7111, {"action_name": action_name})
        
        # Also add to local favorites list
        actions = load_custom_actions()
        if action_name not in actions:
            actions.append(action_name)
            save_custom_actions(actions)
        
        return {"success": True, "data": result, "action_name": action_name}
    except Exception as e:
        logger.error(f"Save action failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/teach/delete_action")
async def delete_recorded_action(request: Request):
    """Delete a saved action (API 7112)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Robot not connected"}
    
    try:
        data = await request.json()
        action_name = data.get("action_name", "").strip()
        
        if not action_name:
            return {"success": False, "error": "action_name required"}
        
        result = await robot.send_api_command(7112, {"action_name": action_name})
        
        # Remove from local favorites list
        actions = load_custom_actions()
        if action_name in actions:
            actions.remove(action_name)
            save_custom_actions(actions)
        
        return {"success": True, "data": result, "action_name": action_name}
    except Exception as e:
        logger.error(f"Delete action failed: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/teach/action_list")
async def get_teach_action_list():
    """Get list of all recorded actions from robot (API 7107)"""
    global robot
    
    if not robot or not robot.connected:
        # Return local favorites if robot not connected
        actions = load_custom_actions()
        return {"success": True, "actions": actions, "source": "local"}
    
    try:
        result = await robot.get_custom_action_list()
        
        if result.get("success"):
            # Parse the action list from robot response
            actions_data = result.get("data")
            if actions_data and isinstance(actions_data, dict):
                # Extract action names from response
                # Format might be: {"actions": ["action1", "action2"]} or similar
                actions = actions_data.get("actions", actions_data.get("action_list", []))
            else:
                # Fallback to local favorites
                actions = load_custom_actions()
            
            return {"success": True, "actions": actions, "source": "robot"}
        else:
            # Fallback to local favorites
            actions = load_custom_actions()
            return {"success": True, "actions": actions, "source": "local"}
    except Exception as e:
        logger.error(f"Get action list failed: {e}")
        # Fallback to local favorites
        actions = load_custom_actions()
        return {"success": True, "actions": actions, "source": "local"}


# Teach mode page route
@app.get("/teach", response_class=HTMLResponse)
async def teach_mode_page():
    """Serve the teach mode page"""
    try:
        with open("teach_mode.html", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load teach mode page: {e}")
        return "<h1>Error loading teach mode page</h1>"


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
        result = await robot.executor.get_action_list()
        # The robot returns action list data - we need to parse the response
        logger.info(f"Robot action list response: {result}")
        return {
            "success": True,
            "data": result  # Return raw data for now, will parse after seeing format
        }
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


# ============================================================================
# LiDAR Status Endpoint
# ============================================================================

@app.get("/api/lidar/status")
async def get_lidar_status():
    """Get LiDAR status"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    lidar_active = robot.state_machine.current_state.lidar_active
    
    return {
        "success": True,
        "active": lidar_active,
        "topic": "rt/utlidar/cloud_livox_mid360",
        "frequency": "10Hz" if lidar_active else "N/A"
    }


# ========================================================================
# Teaching Mode API Endpoints (WebRTC via datachannel)
# ========================================================================

@app.post("/api/teaching/list")
async def teaching_list():
    """Query teaching actions via UDP"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        import socket
        import struct
        import zlib
        
        # Build 0x1A packet
        packet = bytearray()
        packet.append(0x17)
        packet.extend([0xFE, 0xFD, 0x00])
        packet.extend([0x01, 0x00])
        packet.extend([0x00, 0x00])
        packet.extend([0x00, 0x00])
        packet.extend([0x00, 0x01])
        packet.append(0x1A)  # LIST command
        
        payload = bytes(44)
        packet.extend(struct.pack('>H', len(payload)))
        packet.extend(payload)
        
        crc = zlib.crc32(packet) & 0xFFFFFFFF
        packet.extend(struct.pack('>I', crc))
        
        logger.info(f"📋 Sending 0x1A LIST command to {robot.robot_ip}:49504")
        
        # Send via UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.sendto(bytes(packet), (robot.robot_ip, 49504))
        
        # Try to receive response
        try:
            response, _ = sock.recvfrom(4096)
            logger.info(f"✅ Got response: {len(response)} bytes")
            return {"success": True, "response_size": len(response)}
        except socket.timeout:
            logger.warning("No response from robot (timeout)")
            return {"success": True, "sent": True, "response": None}
        finally:
            sock.close()
            
    except Exception as e:
        logger.error(f"Teaching list failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/teaching/enter_damping")
async def teaching_enter_damping():
    """Enter damping/teaching mode (command 0x0D)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.enter_teaching_mode()
        return {"success": True, "result": result, "message": "Robot entered damping mode - it is now compliant"}
    except Exception as e:
        logger.error(f"Enter teaching mode failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/teaching/exit_damping")
async def teaching_exit_damping():
    """Exit damping/teaching mode (command 0x0E)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.exit_teaching_mode()
        return {"success": True, "result": result, "message": "Robot exited damping mode"}
    except Exception as e:
        logger.error(f"Exit teaching mode failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/teaching/start_record")
async def teaching_start_record():
    """Start recording trajectory (command 0x0F)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.start_recording()
        return {"success": True, "result": result, "message": "Recording started"}
    except Exception as e:
        logger.error(f"Start recording failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/teaching/stop_record")
async def teaching_stop_record():
    """Stop recording trajectory (command 0x0F toggle)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.stop_recording()
        return {"success": True, "result": result, "message": "Recording stopped"}
    except Exception as e:
        logger.error(f"Stop recording failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/teaching/save")
async def teaching_save(action_name: str, duration_ms: int = 0):
    """Save teaching action (command 0x2B)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.save_teaching_action(action_name, duration_ms)
        return {"success": True, "result": result, "message": f"Saved action '{action_name}'"}
    except Exception as e:
        logger.error(f"Save teaching action failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/teaching/play")
async def teaching_play(action_id: int = 1):
    """Play teaching action (command 0x41)"""
    global robot
    
    if not robot or not robot.connected:
        return {"success": False, "error": "Not connected"}
    
    try:
        result = await robot.executor.play_teaching_action(action_id)
        return {"success": True, "result": result, "message": f"Playing action {action_id}"}
    except Exception as e:
        logger.error(f"Play teaching action failed: {e}", exc_info=True)
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


def main():
    """Run the web server"""
    logger.info("Starting G1 Web UI Server")
    logger.info("Open http://localhost:9000 in your browser")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
