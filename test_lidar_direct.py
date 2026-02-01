#!/usr/bin/env python3
"""Test LiDAR subscription directly"""

import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
sys.path.insert(0, '/root/G1/unitree_sdk2')

from go2_webrtc_connect.webrtc_driver import Go2WebRTCConnection
import time

def main():
    # Connect to robot
    print("🔌 Connecting to robot...")
    conn = Go2WebRTCConnection()
    conn.connect('192.168.86.18')
    time.sleep(2)
    print("✅ Connected")
    
    # Subscribe to LiDAR
    received = []
    def lidar_callback(msg):
        received.append(msg)
        print(f'\n=== LiDAR Message #{len(received)} ===')
        print(f'Type: {type(msg)}')
        
        if isinstance(msg, dict):
            print(f'Keys: {list(msg.keys())}')
            
            if 'data' in msg:
                data = msg['data']
                print(f'Data type: {type(data)}')
                
                if isinstance(data, dict):
                    print(f'Data keys: {list(data.keys())[:15]}')
                    
                    # Check for common PointCloud2 fields
                    if 'header' in data:
                        print(f'  header: {data["header"]}')
                    if 'height' in data:
                        print(f'  height: {data["height"]}')
                    if 'width' in data:
                        print(f'  width: {data["width"]}')
                    if 'fields' in data:
                        print(f'  fields: {data["fields"][:3]}...')
                    if 'is_bigendian' in data:
                        print(f'  is_bigendian: {data["is_bigendian"]}')
                    if 'point_step' in data:
                        print(f'  point_step: {data["point_step"]}')
                    if 'row_step' in data:
                        print(f'  row_step: {data["row_step"]}')
                    if 'data' in data:
                        data_bytes = data['data']
                        if isinstance(data_bytes, (list, bytes)):
                            print(f'  data length: {len(data_bytes)} bytes')
                        else:
                            print(f'  data type: {type(data_bytes)}')
                    if 'is_dense' in data:
                        print(f'  is_dense: {data["is_dense"]}')
                        
                elif isinstance(data, (list, bytes)):
                    print(f'Data length: {len(data)} bytes')
                    
        print(f'First 500 chars: {str(msg)[:500]}...')
        print('=' * 80)
    
    print("\n📡 Subscribing to rt/utlidar/cloud_livox_mid360")
    conn.datachannel.pub_sub.subscribe('rt/utlidar/cloud_livox_mid360', lidar_callback)
    
    print("⏳ Waiting for LiDAR data (15 seconds)...\n")
    time.sleep(15)
    
    print(f'\n📊 Total messages received: {len(received)}')
    
    if len(received) == 0:
        print("❌ NO LiDAR DATA RECEIVED!")
        print("   Possible causes:")
        print("   - LiDAR not enabled on robot")
        print("   - Wrong topic name")
        print("   - Robot model doesn't have LiDAR")
    else:
        print("✅ LiDAR data is being received!")
    
if __name__ == '__main__':
    main()
