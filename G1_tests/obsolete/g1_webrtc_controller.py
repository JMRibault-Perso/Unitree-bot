#!/usr/bin/env python3
"""
G1 Air WebRTC Controller
Full control interface for Unitree G1 using WebRTC API
Based on unitree_webrtc_connect examples
"""

import asyncio
import logging
import sys

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

class G1Controller:
    """G1 robot controller via WebRTC"""
    
    # Arm action IDs from example
    ARM_ACTIONS = {
        "handshake": 27,
        "high_five": 18,
        "hug": 19,
        "high_wave": 26,
        "clap": 17,
        "face_wave": 25,
        "left_kiss": 12,
        "arm_heart": 20,
        "right_heart": 21,
        "hands_up": 15,
        "xray": 24,
        "right_hand_up": 23,
        "reject": 22,
        "cancel": 99  # Return to neutral
    }
    
    # Sport modes
    SPORT_MODES = {
        "walk": 500,
        "walk_control_waist": 501,
        "run": 801
    }
    
    def __init__(self, connection):
        self.conn = connection
        
    async def arm_action(self, action_name, wait_time=5):
        """Execute arm action"""
        if action_name not in self.ARM_ACTIONS:
            print(f"Unknown action: {action_name}")
            print(f"Available: {', '.join(self.ARM_ACTIONS.keys())}")
            return
        
        action_id = self.ARM_ACTIONS[action_name]
        print(f"Executing arm action: {action_name}")
        
        await self.conn.datachannel.pub_sub.publish_request_new(
            "rt/api/arm/request",
            {
                "api_id": 7106,
                "parameter": {"data": action_id}
            }
        )
        
        await asyncio.sleep(wait_time)
        
    async def set_sport_mode(self, mode_name, wait_time=3):
        """Set locomotion mode"""
        if mode_name not in self.SPORT_MODES:
            print(f"Unknown mode: {mode_name}")
            print(f"Available: {', '.join(self.SPORT_MODES.keys())}")
            return
        
        mode_id = self.SPORT_MODES[mode_name]
        print(f"Switching to mode: {mode_name}")
        
        await self.conn.datachannel.pub_sub.publish_request_new(
            "rt/api/sport/request",
            {
                "api_id": 7101,
                "parameter": {"data": mode_id}
            }
        )
        
        await asyncio.sleep(wait_time)
        
    async def move(self, lx=0.0, ly=0.0, rx=0.0, ry=0.0, duration=2.0):
        """
        Send movement command
        
        lx: Left stick X (strafe left/right) -1.0 to 1.0
        ly: Left stick Y (forward/back) -1.0 to 1.0
        rx: Right stick X (turn left/right) -1.0 to 1.0
        ry: Right stick Y (pitch control) -1.0 to 1.0
        """
        print(f"Moving: lx={lx:.2f}, ly={ly:.2f}, rx={rx:.2f}, ry={ry:.2f}")
        
        self.conn.datachannel.pub_sub.publish_without_callback(
            "rt/wirelesscontroller",
            {
                "lx": lx,
                "ly": ly,
                "rx": rx,
                "ry": ry,
                "keys": 0
            }
        )
        
        await asyncio.sleep(duration)
        
        # Auto-stop after duration
        await self.stop()
        
    async def stop(self):
        """Stop all movement"""
        print("Stopping movement")
        self.conn.datachannel.pub_sub.publish_without_callback(
            "rt/wirelesscontroller",
            {
                "lx": 0.0,
                "ly": 0.0,
                "rx": 0.0,
                "ry": 0.0,
                "keys": 0
            }
        )

async def interactive_mode(controller):
    """Interactive command-line interface"""
    print("\n" + "=" * 60)
    print("G1 Interactive Controller")
    print("=" * 60)
    print("\nCommands:")
    print("  ARM ACTIONS:")
    print("    wave, handshake, high_five, hug, clap, hands_up")
    print("  MODES:")
    print("    walk, run")
    print("  MOVEMENT:")
    print("    forward, back, left, right, turn_left, turn_right")
    print("  CONTROL:")
    print("    stop, reset, quit")
    print("-" * 60)
    
    while True:
        try:
            cmd = input("\nG1> ").strip().lower()
            
            if not cmd:
                continue
                
            if cmd in ["quit", "exit", "q"]:
                print("Exiting...")
                break
                
            # Arm actions
            elif cmd in controller.ARM_ACTIONS:
                await controller.arm_action(cmd)
                
            elif cmd == "reset":
                await controller.arm_action("cancel")
                
            # Modes
            elif cmd in controller.SPORT_MODES:
                await controller.set_sport_mode(cmd)
                
            # Movement commands
            elif cmd == "forward":
                await controller.move(ly=0.5, duration=2.0)
            elif cmd == "back":
                await controller.move(ly=-0.5, duration=2.0)
            elif cmd == "left":
                await controller.move(lx=-0.5, duration=2.0)
            elif cmd == "right":
                await controller.move(lx=0.5, duration=2.0)
            elif cmd == "turn_left":
                await controller.move(rx=-0.5, duration=2.0)
            elif cmd == "turn_right":
                await controller.move(rx=0.5, duration=2.0)
            elif cmd == "stop":
                await controller.stop()
                
            # Help
            elif cmd == "help":
                print("\nAvailable arm actions:", ", ".join(controller.ARM_ACTIONS.keys()))
                print("Available modes:", ", ".join(controller.SPORT_MODES.keys()))
                
            else:
                print(f"Unknown command: {cmd} (type 'help' for commands)")
                
        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except Exception as e:
            print(f"Error: {e}")

async def demo_sequence(controller):
    """Run a demonstration sequence"""
    print("\n" + "=" * 60)
    print("Running G1 Demo Sequence")
    print("=" * 60)
    
    # Wave hello
    print("\n1. Waving hello...")
    await controller.arm_action("high_wave", wait_time=4)
    await controller.arm_action("cancel", wait_time=2)
    
    # Switch to walk mode
    print("\n2. Switching to walk mode...")
    await controller.set_sport_mode("walk", wait_time=3)
    
    # Walk forward
    print("\n3. Walking forward...")
    await controller.move(ly=0.3, duration=3.0)
    
    # Turn around
    print("\n4. Turning around...")
    await controller.move(rx=0.5, duration=3.0)
    
    # Walk back
    print("\n5. Walking back...")
    await controller.move(ly=0.3, duration=3.0)
    
    # Wave goodbye
    print("\n6. Waving goodbye...")
    await controller.arm_action("face_wave", wait_time=4)
    await controller.arm_action("cancel", wait_time=2)
    
    print("\n✓ Demo sequence complete!")

async def main():
    """Main entry point"""
    
    print("=" * 60)
    print("G1 Air WebRTC Controller")
    print("=" * 60)
    
    # Connection setup
    print("\nConnection Method:")
    print("1. LocalSTA (robot on same WiFi)")
    print("2. LocalAP (robot hotspot)")
    print("3. Remote (via cloud)")
    
    choice = input("\nSelect [1/2/3, default=1]: ").strip() or "1"
    
    try:
        # Create connection
        if choice == "1":
            print("\nLocalSTA Options:")
            print("1. By IP address")
            print("2. By serial number (recommended)")
            local_opt = input("Select [1/2, default=2]: ").strip() or "2"
            
            if local_opt == "1":
                ip = input("Robot IP [192.168.86.3]: ").strip() or "192.168.86.3"
                conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=ip)
            else:
                serial = input("Serial number [E21D1000PAHBMB06]: ").strip() or "E21D1000PAHBMB06"
                conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber=serial)
        elif choice == "2":
            conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
        elif choice == "3":
            serial = input("Robot serial [E21D1000PAHBMB06]: ").strip() or "E21D1000PAHBMB06"
            username = input("Unitree email: ").strip()
            password = input("Password: ").strip()
            conn = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.Remote,
                serialNumber=serial,
                username=username,
                password=password
            )
        else:
            print("Invalid choice")
            return
        
        # Connect
        print("\nConnecting to G1...")
        await conn.connect()
        print("✓ Connected!")
        
        # Create controller
        controller = G1Controller(conn)
        
        # Mode selection
        print("\nMode:")
        print("1. Interactive control")
        print("2. Run demo sequence")
        
        mode = input("\nSelect [1/2, default=1]: ").strip() or "1"
        
        if mode == "1":
            await interactive_mode(controller)
        elif mode == "2":
            await demo_sequence(controller)
            # Keep connection alive
            await asyncio.sleep(5)
        
    except ValueError as e:
        print(f"\n✗ Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logging.exception("Details:")
        sys.exit(1)
    finally:
        print("\nDisconnected.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
