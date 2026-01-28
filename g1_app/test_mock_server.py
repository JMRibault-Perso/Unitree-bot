#!/usr/bin/env python3
"""
Mock Robot Server for Testing State Machine and UI
Simulates robot responses without real hardware
"""

import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from enum import IntEnum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FSMState(IntEnum):
    ZERO_TORQUE = 0
    DAMP = 1
    SQUAT = 2
    STAND_UP = 3
    START = 4
    SQUAT_TO_STAND = 5
    SIT = 6
    LOCK_STAND = 500  # WALK mode
    LOCK_STAND_ADV = 501  # WALK-3DOF
    RUN = 801


class MockRobot:
    """Simulates robot state and behavior"""
    
    TRANSITIONS = {
        FSMState.ZERO_TORQUE: [FSMState.ZERO_TORQUE, FSMState.DAMP],
        FSMState.DAMP: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.SQUAT_TO_STAND, 
                        FSMState.SQUAT, FSMState.SIT, FSMState.START, FSMState.STAND_UP],
        FSMState.SQUAT_TO_STAND: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.SQUAT, FSMState.STAND_UP],
        FSMState.SQUAT: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.SQUAT, FSMState.SQUAT_TO_STAND],
        FSMState.STAND_UP: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.STAND_UP, FSMState.START],
        FSMState.START: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.START, FSMState.LOCK_STAND],
        FSMState.SIT: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.SIT],
        FSMState.LOCK_STAND: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.LOCK_STAND, FSMState.RUN],
        FSMState.LOCK_STAND_ADV: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.LOCK_STAND_ADV, FSMState.RUN],
        FSMState.RUN: [FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.RUN, FSMState.LOCK_STAND],
    }
    
    LED_COLORS = {
        FSMState.ZERO_TORQUE: "purple",
        FSMState.DAMP: "orange",
        FSMState.SQUAT: "blue",
        FSMState.SQUAT_TO_STAND: "cyan",
        FSMState.STAND_UP: "yellow",
        FSMState.START: "white",
        FSMState.SIT: "pink",
        FSMState.LOCK_STAND: "green",
        FSMState.LOCK_STAND_ADV: "green",
        FSMState.RUN: "green",
    }
    
    def __init__(self):
        self.fsm_state = FSMState.ZERO_TORQUE
        self.fsm_mode = 0
        self.battery_soc = 95
        self.battery_voltage = 106.5
        self.battery_current = -1400
        self.battery_temp = 23
        self.connected = False
        
    def get_state(self) -> Dict:
        """Get current robot state"""
        allowed = [FSMState(s).name for s in self.TRANSITIONS.get(self.fsm_state, [])]
        return {
            "fsm_state": self.fsm_state.name,
            "fsm_state_value": self.fsm_state.value,
            "fsm_mode": self.fsm_mode,
            "led_color": self.LED_COLORS.get(self.fsm_state, "blue"),
            "allowed_transitions": allowed
        }
    
    def get_battery(self) -> Dict:
        """Get battery state"""
        return {
            "soc": self.battery_soc,
            "voltage": self.battery_voltage,
            "current": self.battery_current / 1000.0,
            "temperature": self.battery_temp
        }
    
    def set_state(self, state_name: str) -> bool:
        """Attempt state transition"""
        try:
            new_state = FSMState[state_name]
            allowed = self.TRANSITIONS.get(self.fsm_state, [])
            
            if new_state in allowed:
                logger.info(f"State transition: {self.fsm_state.name} → {new_state.name}")
                self.fsm_state = new_state
                return True
            else:
                logger.warning(f"Invalid transition: {self.fsm_state.name} → {state_name}")
                return False
        except KeyError:
            logger.error(f"Unknown state: {state_name}")
            return False
    
    def update_battery(self):
        """Simulate battery drain"""
        if self.battery_soc > 0:
            self.battery_soc = max(0, self.battery_soc - 0.01)
            self.battery_voltage = 100 + (self.battery_soc * 0.1)


# Mock robot instance
robot = MockRobot()

# WebSocket connections
connections = []

app = FastAPI(title="Mock Robot Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for UI
from fastapi.staticfiles import StaticFiles
import os
ui_dir = os.path.join(os.path.dirname(__file__), "ui")
if os.path.exists(ui_dir):
    app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")


@app.get("/")
async def root():
    return {"status": "Mock Robot Server Running", "state": robot.get_state()}


@app.post("/api/connect")
async def connect(ip: str, serial_number: str):
    """Mock connection"""
    robot.connected = True
    logger.info(f"Mock connection to {serial_number} at {ip}")
    
    # Broadcast connection event
    await broadcast({
        "type": "connection_changed",
        "data": {"connected": True}
    })
    
    return {
        "success": True,
        "state": robot.get_state()
    }


@app.post("/api/disconnect")
async def disconnect():
    """Mock disconnect"""
    robot.connected = False
    logger.info("Mock disconnect")
    
    await broadcast({
        "type": "connection_changed",
        "data": {"connected": False}
    })
    
    return {"success": True}


@app.get("/api/state")
async def get_state():
    """Get current state"""
    return {
        "success": True,
        "state": robot.get_state()
    }


@app.post("/api/set_state")
async def set_state(state_name: str):
    """Set FSM state"""
    success = robot.set_state(state_name)
    
    if success:
        # Broadcast state change
        await broadcast({
            "type": "state_changed",
            "data": robot.get_state()
        })
        
        return {"success": True, "state": robot.get_state()}
    else:
        return {
            "success": False,
            "error": f"Invalid transition from {robot.fsm_state.name} to {state_name}"
        }


@app.post("/api/move")
async def move(vx: float = 0, vy: float = 0, omega: float = 0):
    """Mock movement"""
    logger.info(f"Mock move: vx={vx}, vy={vy}, omega={omega}")
    return {"success": True}


@app.post("/api/gesture")
async def gesture(gesture_name: str):
    """Mock gesture"""
    logger.info(f"Mock gesture: {gesture_name}")
    return {"success": True, "message": f"Executed {gesture_name}"}


@app.get("/api/discover")
async def discover():
    """Mock robot discovery"""
    return {
        "success": True,
        "robots": [{
            "name": "MOCK_G1_TEST",
            "serial_number": "MOCK_12345",
            "ip": "127.0.0.1",
            "is_bound": True,
            "is_online": True,
            "last_seen": "2026-01-25T15:00:00"
        }],
        "bound_count": 1
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    connections.append(websocket)
    logger.info(f"WebSocket connected. Total connections: {len(connections)}")
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except Exception as e:
        logger.info(f"WebSocket disconnected: {e}")
    finally:
        connections.remove(websocket)


async def broadcast(message: Dict):
    """Broadcast message to all WebSocket connections"""
    for connection in connections[:]:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send to connection: {e}")
            connections.remove(connection)


async def battery_update_task():
    """Simulate battery updates"""
    while True:
        await asyncio.sleep(2)
        if robot.connected:
            robot.update_battery()
            await broadcast({
                "type": "battery_updated",
                "data": robot.get_battery()
            })


@app.on_event("startup")
async def startup():
    """Start background tasks"""
    logger.info("Starting mock robot server...")
    asyncio.create_task(battery_update_task())


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 MOCK ROBOT SERVER")
    print("="*60)
    print("This server simulates a G1 robot for testing")
    print("Access at: http://localhost:8080")
    print("Use the regular UI at: http://localhost:8080/ui/index.html")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
