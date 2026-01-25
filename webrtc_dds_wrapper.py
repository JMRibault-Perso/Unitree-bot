#!/usr/bin/env python3
"""
WebRTC-DDS Wrapper for Unitree G1

Based on discovery that WebRTC wraps DDS commands:
- WebRTC provides transport layer (STUN for P2P connection)
- DDS messages are sent through WebRTC data channels
- Topics from unitree_sdk2 can be used via WebRTC

This bridges unitree_sdk2 (DDS messages) with unitree_webrtc_connect (transport)
"""

import sys
import os
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import (
    UnitreeWebRTCConnection,
    WebRTCConnectionMethod
)
from unitree_webrtc_connect.constants import RTC_TOPIC, DATA_CHANNEL_TYPE
import json
import time

class WebRTCDDSBridge:
    """
    Bridge between DDS messages (unitree_sdk2) and WebRTC transport
    
    Usage:
        bridge = WebRTCDDSBridge()
        bridge.connect()
        bridge.send_low_cmd(dds_lowcmd_message)
        state = bridge.get_low_state()
    """
    
    def __init__(self, robot_ip="192.168.86.16", device_name="G1_6937", 
                 email="sebastianribault1@gmail.com", password="Xlp142!?rz"):
        self.robot_ip = robot_ip
        self.device_name = device_name
        self.email = email
        self.password = password
        self.connection = None
        self.subscriptions = {}
        
    def connect(self, method="local"):
        """
        Connect to robot via WebRTC
        
        Args:
            method: "local" for LocalSTA, "cloud" for Remote
        """
        print(f"Connecting to {self.device_name} at {self.robot_ip}...")
        
        if method == "local":
            # Try local STUN connection (port 44932)
            self.connection = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.LocalSTA,
                robot_ip=self.robot_ip
            )
        else:
            # Use cloud relay
            self.connection = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.Remote,
                username=self.email,
                password=self.password,
                device_name=self.device_name
            )
        
        # Initialize connection
        if self.connection.connect():
            print(f"✓ Connected via {'local' if method == 'local' else 'cloud'} WebRTC")
            return True
        else:
            print("✗ Connection failed")
            return False
    
    def subscribe_topic(self, topic_name, callback):
        """
        Subscribe to a DDS topic via WebRTC data channel
        
        Args:
            topic_name: DDS topic (e.g., RTC_TOPIC["LOW_STATE"])
            callback: Function to call with received data
        """
        if not self.connection:
            print("Not connected!")
            return False
        
        # Send subscribe message through WebRTC data channel
        subscribe_msg = {
            "type": DATA_CHANNEL_TYPE["SUBSCRIBE"],
            "topic": topic_name
        }
        
        self.connection.send_data_channel_message(json.dumps(subscribe_msg))
        self.subscriptions[topic_name] = callback
        print(f"Subscribed to {topic_name}")
        return True
    
    def publish_topic(self, topic_name, data):
        """
        Publish to a DDS topic via WebRTC data channel
        
        Args:
            topic_name: DDS topic (e.g., RTC_TOPIC["LOW_CMD"])
            data: DDS message (dict or serialized bytes)
        """
        if not self.connection:
            print("Not connected!")
            return False
        
        # Wrap DDS message in WebRTC data channel format
        publish_msg = {
            "type": DATA_CHANNEL_TYPE["MSG"],
            "topic": topic_name,
            "data": data
        }
        
        self.connection.send_data_channel_message(json.dumps(publish_msg))
        return True
    
    def send_low_cmd(self, cmd_data):
        """
        Send LowCmd (motor control) via WebRTC
        
        Args:
            cmd_data: DDS LowCmd message (from unitree_sdk2)
        """
        return self.publish_topic(RTC_TOPIC["LOW_CMD"], cmd_data)
    
    def send_sport_cmd(self, cmd_data):
        """
        Send Sport Mode command (walk, stand, etc.)
        
        Args:
            cmd_data: Sport mode command dict
        """
        return self.publish_topic(RTC_TOPIC["SPORT_MOD"], cmd_data)
    
    def send_arm_cmd(self, cmd_data):
        """
        Send Arm control command
        
        Args:
            cmd_data: Arm command dict
        """
        return self.publish_topic(RTC_TOPIC["ARM_COMMAND"], cmd_data)
    
    def get_low_state(self, callback):
        """Subscribe to robot low-level state"""
        return self.subscribe_topic(RTC_TOPIC["LOW_STATE"], callback)
    
    def get_sport_state(self, callback):
        """Subscribe to sport mode state"""
        return self.subscribe_topic(RTC_TOPIC["SPORT_MOD_STATE"], callback)
    
    def disconnect(self):
        """Close WebRTC connection"""
        if self.connection:
            self.connection.disconnect()
            print("Disconnected")

# Example commands from unitree_sdk2 documentation
SPORT_COMMANDS = {
    "stand": {"api_id": 1001},  # Stand up
    "stand_down": {"api_id": 1002},  # Stand down
    "zero_torque": {"api_id": 1013},  # Zero torque mode
    "damp": {"api_id": 1008},  # Damp mode
    "move": {"api_id": 1008, "x": 0.0, "y": 0.0, "z": 0.0},  # Move command
    "hello": {"api_id": 1016},  # Wave gesture
}

def test_connection():
    """Test basic WebRTC-DDS connection"""
    bridge = WebRTCDDSBridge(
        robot_ip="192.168.86.16",
        device_name="G1_6937"
    )
    
    # Try local connection first
    if not bridge.connect(method="local"):
        print("Local connection failed, trying cloud...")
        if not bridge.connect(method="cloud"):
            print("Both connections failed!")
            return
    
    # Subscribe to robot state
    def on_state_update(data):
        print(f"State update: {data}")
    
    bridge.get_low_state(on_state_update)
    
    # Send zero torque command
    print("\nSending zero torque command...")
    bridge.send_sport_cmd(SPORT_COMMANDS["zero_torque"])
    
    time.sleep(5)
    
    # Send stand command
    print("\nSending stand command...")
    bridge.send_sport_cmd(SPORT_COMMANDS["stand"])
    
    time.sleep(5)
    bridge.disconnect()

def interactive_control():
    """Interactive command sender"""
    bridge = WebRTCDDSBridge()
    
    if not bridge.connect(method="local"):
        bridge.connect(method="cloud")
    
    print("\nAvailable commands:")
    for name in SPORT_COMMANDS.keys():
        print(f"  - {name}")
    print("  - quit")
    
    while True:
        cmd = input("\nEnter command: ").strip()
        
        if cmd == "quit":
            break
        
        if cmd in SPORT_COMMANDS:
            bridge.send_sport_cmd(SPORT_COMMANDS[cmd])
            print(f"Sent: {cmd}")
        else:
            print(f"Unknown command: {cmd}")
    
    bridge.disconnect()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='WebRTC-DDS Bridge for Unitree G1')
    parser.add_argument('--test', action='store_true', help='Run connection test')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--ip', default='192.168.86.16', help='Robot IP')
    parser.add_argument('--device', default='G1_6937', help='Device name')
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
    elif args.interactive:
        interactive_control()
    else:
        print("WebRTC-DDS Bridge")
        print("\nThis bridges unitree_sdk2 DDS messages with WebRTC transport")
        print("\nDDS Topics available via WebRTC:")
        for name, topic in RTC_TOPIC.items():
            print(f"  {name}: {topic}")
        print("\nUsage:")
        print("  python3 webrtc_dds_wrapper.py --test         # Test connection")
        print("  python3 webrtc_dds_wrapper.py --interactive  # Interactive control")
        print("\nIn your code:")
        print("  from webrtc_dds_wrapper import WebRTCDDSBridge")
        print("  bridge = WebRTCDDSBridge()")
        print("  bridge.connect()")
        print("  bridge.send_sport_cmd({'api_id': 1001})  # Stand")
