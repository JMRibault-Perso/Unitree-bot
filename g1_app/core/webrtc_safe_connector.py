"""
Safe WebRTC connector - wraps UnitreeWebRTCConnection in subprocess to prevent crashes
"""

import asyncio
import logging
import subprocess
import json
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class SafeWebRTCConnector:
    """
    Wraps WebRTC connection in a subprocess to isolate crashes
    """
    
    def __init__(self, ip: str, serial_number: str):
        self.ip = ip
        self.serial_number = serial_number
        self.process = None
        self.datachannel = None
        
    async def connect(self):
        """Connect to robot safely in subprocess"""
        # Create a temporary script to run the connection in subprocess
        script = f"""
import sys
import asyncio
import os
from pathlib import Path

# Add WebRTC library paths (Linux and Windows)
project_root = r'{project_root}'
webrtc_paths = [
    '/root/G1/go2_webrtc_connect',  # Linux
    str(Path(project_root) / 'libs' / 'go2_webrtc_connect'),  # Windows
]
for path in webrtc_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
import json

async def main():
    try:
        print("SUBPROCESS_START", flush=True)
        
        # Try Local STA
        try:
            print("TRY_LOCALSTA", flush=True)
            conn = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.LocalSTA,
                ip="{self.ip}",
                serialNumber="{self.serial_number}"
            )
            await conn.connect()
            print("CONNECTED_LOCALSTA", flush=True)
            return conn
        except Exception as e:
            print(f"LOCALSTA_FAILED:{str(e)}", flush=True)
            
            # Try cloud
            try:
                print("TRY_REMOTE", flush=True)
                conn = UnitreeWebRTCConnection(
                    WebRTCConnectionMethod.Remote,
                    serialNumber="{self.serial_number}",
                    username="sebastianribault1@gmail.com",
                    password="Xlp142!?rz"
                )
                await conn.connect()
                print("CONNECTED_REMOTE", flush=True)
                return conn
            except Exception as e2:
                print(f"REMOTE_FAILED:{str(e2)}", flush=True)
                return None
    except Exception as e:
        print(f"SUBPROCESS_ERROR:{str(e)}", flush=True)
        return None

asyncio.run(main())
"""
        
        try:
            # Run script in subprocess
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            try:
                # Run subprocess with timeout
                process = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        'python', script_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    ),
                    timeout=30
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30
                )
                
                output = stdout.decode('utf-8', errors='replace')
                errors = stderr.decode('utf-8', errors='replace')
                
                logger.info(f"WebRTC subprocess output: {output}")
                if errors:
                    logger.warning(f"WebRTC subprocess errors: {errors}")
                
                if "CONNECTED_LOCALSTA" in output or "CONNECTED_REMOTE" in output:
                    logger.info("✅ WebRTC connection successful in subprocess")
                    self.datachannel = MockDataChannel()  # Placeholder
                    return True
                else:
                    logger.error(f"WebRTC connection failed: {output}")
                    raise ConnectionError(f"WebRTC connection failed: {output}")
                    
            finally:
                # Clean up temporary script
                if os.path.exists(script_path):
                    os.remove(script_path)
                    
        except asyncio.TimeoutError:
            raise ConnectionError("WebRTC connection timed out")
        except Exception as e:
            raise ConnectionError(f"WebRTC subprocess error: {e}")
    
    async def disconnect(self):
        """Disconnect from robot"""
        pass


class MockDataChannel:
    """Mock datachannel for now"""
    
    class PubSub:
        async def publish_request_new(self, topic, data):
            pass
    
    def __init__(self):
        self.pub_sub = self.PubSub()
