#!/bin/bash
# Comprehensive DDS Diagnostic Script for G1 Robot
# Based on: https://support.unitree.com/home/en/G1_developer/dds_communication_routine

ROBOT_IP="192.168.86.3"
ROBOT_NAME="G1_6937"

echo "=========================================="
echo "  G1 DDS Communication Diagnostics"
echo "=========================================="
echo "Robot: $ROBOT_NAME"
echo "Robot IP: $ROBOT_IP"
echo ""

# Step 1: Network connectivity
echo "=== Step 1: Network Connectivity ==="
echo -n "Pinging robot... "
if ping -c 2 -W 2 $ROBOT_IP > /dev/null 2>&1; then
    echo "✓ SUCCESS"
else
    echo "✗ FAILED - Robot not reachable on network"
    echo "  Check: Is robot powered on and connected to WiFi?"
    echo "  Check: Are you on the same WiFi network (192.168.86.x)?"
    exit 1
fi
echo ""

# Step 2: Identify network interface
echo "=== Step 2: Network Interface Detection ==="
echo "Available network interfaces:"
ip -br addr show | grep -v "^lo" | while read iface state addr rest; do
    if [[ $addr == *"192.168.86."* ]]; then
        echo "  $iface: $addr  ← SAME SUBNET AS ROBOT ✓"
        DETECTED_IFACE=$iface
    else
        echo "  $iface: $addr"
    fi
done

# Try to detect the correct interface automatically
IFACE=$(ip -br addr show | grep "192.168.86." | awk '{print $1}' | head -1)
if [ -z "$IFACE" ]; then
    echo ""
    echo "⚠ WARNING: No interface found on 192.168.86.x subnet"
    echo "Available interfaces:"
    ip -br addr show | grep -v "^lo"
    echo ""
    read -p "Enter network interface to use (e.g., eth0, eth1, wlan0): " IFACE
else
    echo ""
    echo "Auto-detected interface: $IFACE"
    read -p "Press Enter to use this, or type different interface: " USER_IFACE
    if [ ! -z "$USER_IFACE" ]; then
        IFACE=$USER_IFACE
    fi
fi
echo ""

# Step 3: Environment setup
echo "=== Step 3: Environment Setup ==="
export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml
export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH

echo "CYCLONEDDS_URI=$CYCLONEDDS_URI"
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
echo "Network interface: $IFACE"

if [ ! -f "$(pwd)/cyclonedds.xml" ]; then
    echo "✗ ERROR: cyclonedds.xml not found!"
    exit 1
else
    echo "✓ cyclonedds.xml found"
fi
echo ""

# Step 4: Check if binaries exist
echo "=== Step 4: Binary Availability ==="
if [ -f "./build/bin/test_subscriber" ]; then
    echo "✓ test_subscriber found"
else
    echo "✗ test_subscriber not found - run 'mkdir build && cd build && cmake .. && make'"
    exit 1
fi
echo ""

# Step 5: Listen for robot DDS topics
echo "=== Step 5: DDS Topic Discovery ==="
echo "Listening for DDS messages from robot for 10 seconds..."
echo "If robot is broadcasting, you should see messages like 'rt/lowstate'"
echo ""
echo "--- OUTPUT START ---"
timeout 10 ./build/bin/test_subscriber 2>&1 | tee /tmp/dds_output.txt
echo "--- OUTPUT END ---"
echo ""

# Check if we got any output
if grep -q "Received" /tmp/dds_output.txt 2>/dev/null; then
    echo "✓ SUCCESS - DDS messages received!"
    echo ""
    echo "Next steps:"
    echo "  1. Try: ./build/bin/g1_loco_client --network_interface=$IFACE --get_fsm_mode"
    echo "  2. Try: ./build/bin/test_robot_listener $IFACE"
else
    echo "✗ NO DDS MESSAGES RECEIVED"
    echo ""
    echo "=== Troubleshooting Steps ==="
    echo ""
    echo "1. Check if robot SDK mode is enabled:"
    echo "   - Open Unitree app on Android"
    echo "   - Go to Device settings"
    echo "   - Look for 'Developer Mode' or 'SDK Mode' toggle"
    echo ""
    echo "2. Verify firewall allows UDP ports 7400-7430:"
    echo "   sudo ufw allow 7400:7430/udp"
    echo "   # OR disable firewall temporarily:"
    echo "   sudo ufw disable"
    echo ""
    echo "3. Test with specific network interface:"
    echo "   ./build/bin/test_subscriber $IFACE"
    echo ""
    echo "4. Check multicast routing:"
    echo "   ip maddress show $IFACE"
    echo "   # Should show multicast groups"
    echo ""
    echo "5. If on WSL2, try native Linux instead"
    echo "   WSL2 network virtualization blocks DDS multicast"
    echo ""
    echo "6. Try running test publisher on another terminal:"
    echo "   # Terminal 1:"
    echo "   ./build/bin/publisher $IFACE"
    echo "   # Terminal 2:"
    echo "   ./build/bin/subscriber $IFACE"
    echo ""
fi

echo ""
echo "=========================================="
echo "Diagnostic complete"
echo "=========================================="
