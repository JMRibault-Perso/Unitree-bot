#!/usr/bin/env python3
"""
List all available services on the robot via the running web server
"""

import requests
import json

def query_service_list():
    """Query the web server to list robot services"""
    
    # First check if connected
    status_resp = requests.get('http://localhost:9000/api/status')
    status = status_resp.json()
    
    if not status.get('connected'):
        print("❌ Robot not connected")
        return
    
    print(f"✅ Connected to {status.get('robot_name')} at {status.get('robot_ip')}")
    print("\n🔍 Querying available services...\n")
    
    # Try to get service list
    endpoints_to_try = [
        '/api/services/list',
        '/api/service/list', 
        '/api/robot/services',
        '/api/system/services',
    ]
    
    for endpoint in endpoints_to_try:
        try:
            resp = requests.get(f'http://localhost:9000{endpoint}')
            if resp.status_code == 200:
                print(f"✅ Found service list at {endpoint}:")
                print(json.dumps(resp.json(), indent=2))
                return
        except:
            pass
    
    print("❌ No service list endpoint found")
    print("\n💡 Let me check what services we know about from constants...")
    
    # Check constants
    import sys
    sys.path.insert(0, '/root/G1/unitree_sdk2')
    from g1_app.api.constants import SystemService
    
    print("\n📋 Known services from constants:")
    for attr in dir(SystemService):
        if not attr.startswith('_'):
            value = getattr(SystemService, attr)
            print(f"   - {attr}: {value}")

if __name__ == "__main__":
    query_service_list()
