#!/usr/bin/env python3
"""
CLI Test Interface for G1 Robot Control
Simple command-line interface for testing robot control
"""

import asyncio
import logging
import sys

from g1_app.core import RobotController, EventBus, Events
from g1_app.api import FSMState

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Robot configuration
ROBOT_IP = None  # Will be discovered dynamically
ROBOT_SN = "E21D1000PAHBMB06"


def print_help():
    """Print available commands"""
    print("\n" + "="*60)
    print("G1 ROBOT CONTROLLER - CLI INTERFACE")
    print("="*60)
    print("\nFSM State Commands:")
    print("  d - Damp mode (emergency stop)")
    print("  r - Ready mode (preparatory posture)")
    print("  s - Sit down")
    print("  u - Stand up from squat")
    print()
    print("Motion Commands (requires Ready state):")
    print("  w - Walk forward")
    print("  x - Walk backward")
    print("  a - Strafe left")
    print("  z - Strafe right")
    print("  q - Turn left")
    print("  e - Turn right")
    print("  SPACE - Stop motion")
    print()
    print("Gestures:")
    print("  g - Wave hand")
    print()
    print("System:")
    print("  i - Show current state")
    print("  h - Show this help")
    print("  ctrl+c - Quit")
    print("="*60 + "\n")


async def main():
    """Main CLI loop"""
    controller = RobotController(ROBOT_IP, ROBOT_SN)
    
    # Subscribe to state changes
    def on_state_change(state):
        print(f"\n🤖 Robot State: {state.fsm_state.name} | LED: {state.led_color.value}")
    
    EventBus.subscribe(Events.STATE_CHANGED, on_state_change)
    
    # Connect to robot
    try:
        await controller.connect()
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return
    
    print_help()
    
    # Command loop
    try:
        while True:
            cmd = await asyncio.get_event_loop().run_in_executor(
                None, input, "\nCommand > "
            )
            cmd = cmd.strip().lower()
            
            if not cmd:
                continue
            
            # FSM commands
            if cmd == 'd':
                await controller.damp()
            elif cmd == 'r':
                await controller.ready()
            elif cmd == 's':
                await controller.sit()
            elif cmd == 'u':
                await controller.squat_to_stand()
            
            # Motion commands
            elif cmd == 'w':
                await controller.forward(0.3)
            elif cmd == 'x':
                await controller.backward(0.3)
            elif cmd == 'a':
                await controller.left(0.2)
            elif cmd == 'z':
                await controller.right(0.2)
            elif cmd == 'q':
                await controller.turn_left(0.5)
            elif cmd == 'e':
                await controller.turn_right(0.5)
            elif cmd == ' ':
                await controller.stop()
            
            # Gestures
            elif cmd == 'g':
                await controller.execute_gesture("wave_hand")
            
            # Info
            elif cmd == 'i':
                state = controller.current_state
                print(f"\nCurrent State:")
                print(f"  FSM: {state.fsm_state.name} ({state.fsm_state})")
                print(f"  LED: {state.led_color.value}")
                if state.error:
                    print(f"  ERROR: {state.error}")
            
            # Help
            elif cmd == 'h':
                print_help()
            
            else:
                print(f"Unknown command: {cmd} (press 'h' for help)")
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    
    finally:
        await controller.emergency_stop()
        await controller.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
