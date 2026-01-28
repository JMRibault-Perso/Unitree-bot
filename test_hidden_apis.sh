#!/bin/bash
# Test G1 hidden arm action APIs
# Run this while robot is in RUN mode (standing or walking)
# Does NOT change robot state - safe to test

cd "$(dirname "$0")"

export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml
export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH

echo "======================================"
echo "Testing G1 Arm Action APIs"
echo "======================================"
echo ""
echo "Network interfaces available:"
ip -o link show | awk -F': ' '{print "  - "$2}'
echo ""
read -p "Enter network interface (default: eth1): " IFACE
IFACE=${IFACE:-eth1}

echo ""
echo "Starting test on interface: $IFACE"
echo "Make sure robot is connected and in RUN mode!"
echo ""
read -p "Press ENTER to continue..."

./build/bin/test_arm_apis $IFACE
