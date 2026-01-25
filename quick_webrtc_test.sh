#!/bin/bash
# Quick WebRTC test for G1 E21D1000PAHBMB06

echo "=================================================="
echo "G1 WebRTC Quick Test"
echo "Robot Serial: E21D1000PAHBMB06"
echo "=================================================="
echo ""

# Test 1: Using serial number (auto-discover IP)
echo "Test 1: Connecting via serial number (auto-discover)..."
python3 - <<'PYTHON'
import asyncio
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

async def test():
    try:
        print("Attempting connection via LocalSTA with serial number...")
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA, 
            serialNumber="E21D1000PAHBMB06"
        )
        await conn.connect()
        print("✓ SUCCESS! Connected via serial number")
        await asyncio.sleep(5)
        return True
    except Exception as e:
        print(f"✗ Serial method failed: {e}")
        return False

try:
    result = asyncio.run(test())
    exit(0 if result else 1)
except KeyboardInterrupt:
    print("\nInterrupted")
    exit(1)
PYTHON

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Connection successful!"
    echo "Run the full controller: python3 g1_webrtc_controller.py"
    exit 0
fi

echo ""
echo "Serial number discovery failed. Trying direct IP..."

# Test 2: Try known IP
echo "Test 2: Connecting via IP 192.168.86.3..."
python3 - <<'PYTHON'
import asyncio
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

async def test():
    try:
        print("Attempting connection via LocalSTA with IP...")
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA, 
            ip="192.168.86.3"
        )
        await conn.connect()
        print("✓ SUCCESS! Connected via IP")
        await asyncio.sleep(5)
        return True
    except Exception as e:
        print(f"✗ IP method failed: {e}")
        return False

try:
    result = asyncio.run(test())
    exit(0 if result else 1)
except KeyboardInterrupt:
    print("\nInterrupted")
    exit(1)
PYTHON

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Connection successful!"
    exit 0
fi

echo ""
echo "=================================================="
echo "Both connection methods failed."
echo ""
echo "Possible issues:"
echo "  1. Robot not powered on or in sleep mode"
echo "  2. Robot not connected to WiFi (use Android app to check)"
echo "  3. Robot needs to be in SDK/developer mode"
echo "  4. Try Remote mode (via Unitree cloud)"
echo ""
echo "Next steps:"
echo "  - Check robot status in Android app"
echo "  - Try: python3 g1_webrtc_controller.py"
echo "  - Select Remote mode (requires Unitree account)"
echo "=================================================="
exit 1
