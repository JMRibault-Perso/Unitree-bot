#!/bin/bash
# Simple test to check if we can receive any DDS topics from the G1 robot

export CYCLONEDDS_URI=file:///root/G1/unitree_sdk2/cyclonedds.xml
export LD_LIBRARY_PATH=/root/G1/unitree_sdk2/thirdparty/lib/x86_64:$LD_LIBRARY_PATH

cd /root/G1/unitree_sdk2

echo "=== Testing DDS Communication with G1 Robot ==="
echo "Network: eth1"
echo "Robot IP: 192.168.86.3"
echo ""

# Try to use the built-in test subscriber
echo "Running test subscriber for 5 seconds..."
timeout 5 ./build/bin/test_subscriber 2>&1 | head -20

echo ""
echo "=== Test Complete ==="
echo ""
echo "If you see no output above, the DDS communication is not working."
echo "This is likely due to WSL2's network virtualization blocking DDS multicast."
echo ""
echo "Recommendation: Try running the SDK on a native Linux machine or"
echo "check if the robot has SDK services enabled in the Unitree app."
