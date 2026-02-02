#!/usr/bin/env python3
"""Test script to verify point cloud data flow without restarting server"""
import time
import requests

print("Testing LiDAR point cloud API...")
print("Make sure SLAM is running in the UI!")
print()

for i in range(10):
    try:
        response = requests.get("http://localhost:9000/api/lidar/pointcloud", timeout=2)
        data = response.json()
        count = data.get('count', 0)
        
        if count > 0:
            print(f"✅ SUCCESS! Received {count} points")
            print(f"   Sample point: {data['points'][0] if data.get('points') else 'N/A'}")
            break
        else:
            print(f"⏳ Attempt {i+1}/10: Still 0 points...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(1)
else:
    print("\n❌ FAILED: No points after 10 seconds")
    print("Check /tmp/web_server.log for handler errors")
