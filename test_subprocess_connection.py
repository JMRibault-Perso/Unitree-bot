#!/usr/bin/env python3
"""
Robust connection test with subprocess isolation to handle WebRTC sys.exit() calls
"""

import subprocess
import json
import asyncio
import sys

async def test_subprocess_connection():
    """Test connection in isolated subprocess"""
    
    script = """
import sys
import asyncio
sys.path.insert(0, 'C:/Unitree/G1/go2_webrtc_connect')
sys.path.insert(0, 'C:/Unitree/G1/unitree_sdk2')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

async def main():
    try:
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip="192.168.86.3",
            serialNumber="E21D1000PAHBMB06"
        )
        await asyncio.wait_for(conn.connect(), timeout=15)
        print("SUCCESS")
        return
    except asyncio.TimeoutError:
        print("TIMEOUT_15s")
        return
    except Exception as e:
        print(f"ERROR:{str(e)}")
        return

asyncio.run(main())
"""
    
    # Save script to temp file and run
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("=" * 60)
        print("Subprocess Connection Test")
        print("=" * 60)
        print(f"\nSTDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
        print(f"\nReturn code: {result.returncode}")
        print("\n" + "=" * 60)
        
        if "SUCCESS" in result.stdout:
            print("✅ Connection successful!")
        elif "TIMEOUT" in result.stdout:
            print("⏱️  Connection timed out (port may be closed)")
        else:
            print(f"❌ Connection failed: {result.stdout}")
            
    except subprocess.TimeoutExpired:
        print("❌ Subprocess timed out")
    finally:
        if os.path.exists(script_path):
            os.remove(script_path)

if __name__ == "__main__":
    asyncio.run(test_subprocess_connection())
