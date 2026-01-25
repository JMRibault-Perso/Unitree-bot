#!/usr/bin/env python3
"""
Simple Web UI Server for G1 Robot Control
FastAPI backend with WebSocket for real-time updates
"""

import asyncio
import logging
import socket
import subprocess
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
sys.path.insert(0, '/root/G1/unitree_sdk2')

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
    try:
        # Handle both dict format (from robot_controller) and state object format (from state_machine)
        if isinstance(state, dict):
            # Dictionary format from robot_controller
            data = {
                "fsm_state": state.get("fsm_state_name", "UNKNOWN"),
                "fsm_state_value": state.get("fsm_state", 0),
                "led_color": "blue",  # Default, will be updated by separate LED events
                "error": None,
                "allowed_transitions": []  # Will be populated by API calls
            }
        else:
            # State object format from state_machine
            data = {
                "fsm_state": state.fsm_state.name,
                "fsm_state_value": state.fsm_state.value,
                "led_color": state.led_color.value,
                "error": state.error,
                "allowed_transitions": []  # Will be populated by API calls
            }
        
        asyncio.create_task(manager.broadcast({
            "type": "state_changed",
            "data": data
        }))
    except Exception as e:
        logger.error(f"Error in on_state_change: {e}")
        logger.error(f"State data: {state}, type: {type(state)}")


def on_connection_change(data):
    """Broadcast connection status to all web clients"""
    asyncio.create_task(manager.broadcast({
        "type": "connection_changed",
        "data": data
    }))


# Subscribe to events
EventBus.subscribe(Events.STATE_CHANGED, on_state_change)
EventBus.subscribe(Events.CONNECTION_CHANGED, on_connection_change)


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
        all_robots = discovery.get_robots()
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
        
        # If connected to different robot, disconnect first
        if robot and robot.connected:
            logger.info("Disconnecting from previous robot before new connection")
            try:
                await robot.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting previous robot: {e}")
            robot = None
        
        logger.info(f"Connecting to robot at {ip} (SN: {serial_number})")
        
        # First check if robot is reachable
        import subprocess
        result = subprocess.run(['ping', '-c', '1', '-W', '3', ip], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Robot at {ip} is not reachable on network")
            return {"success": False, "error": f"Robot at {ip} is not reachable. Check if robot is powered on and on same network."}
        
        robot = RobotController(ip, serial_number)
        await robot.connect()
        
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
    """Set FSM state"""
    global robot
    
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
        return {"success": success}
    except Exception as e:
        logger.error(f"Move command failed: {e}")
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


def main():
    """Run the web server"""
    logger.info("Starting G1 Web UI Server")
    logger.info("Open http://localhost:8000 in your browser")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
