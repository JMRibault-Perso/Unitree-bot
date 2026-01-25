#!/bin/bash
# WSL2 DDS Configuration Helper
# Based on reports that Unitree SDK works on WSL2 with proper configuration

echo "=========================================="
echo "  WSL2 DDS Configuration Check"
echo "=========================================="
echo ""

# Check WSL version and Windows version
echo "=== WSL Environment ==="
echo "WSL Version:"
wsl.exe --version 2>/dev/null || echo "  (WSL version command not available)"
echo ""
echo "Kernel:"
uname -r
echo ""

# Check network interfaces
echo "=== Network Interfaces ==="
ip -br addr show | grep -v "^lo"
echo ""

# Check which interface is on same subnet as robot
ROBOT_IP="192.168.86.3"
ROBOT_SUBNET="192.168.86"

echo "=== Robot Connectivity ==="
echo "Robot IP: $ROBOT_IP"
echo "Looking for interfaces on $ROBOT_SUBNET.x subnet:"
MATCHING_IFACE=$(ip -br addr show | grep "$ROBOT_SUBNET" | awk '{print $1}' | head -1)

if [ -z "$MATCHING_IFACE" ]; then
    echo "  ⚠ No interface found on robot's subnet!"
    echo "  Available interfaces:"
    ip -br addr show | grep -v "^lo" | while read iface state addr rest; do
        echo "    $iface: $addr"
    done
else
    echo "  ✓ Found: $MATCHING_IFACE"
    IFACE=$MATCHING_IFACE
fi
echo ""

# Check multicast
echo "=== Multicast Configuration ==="
if [ ! -z "$IFACE" ]; then
    echo "Multicast groups on $IFACE:"
    ip maddress show $IFACE
else
    echo "No interface selected"
fi
echo ""

# Check Windows firewall status
echo "=== Windows Firewall Check ==="
echo "Check Windows Defender Firewall settings:"
echo "  1. Open Windows Security"
echo "  2. Firewall & network protection"
echo "  3. Allow an app through firewall"
echo "  4. Make sure UDP ports 7400-7430 are allowed"
echo ""

# Suggest cyclonedds.xml configurations to try
echo "=== Recommended CycloneDDS Configurations ==="
echo ""
echo "Option 1: Let CycloneDDS auto-detect (current default)"
echo "  <Domain id=\"any\">"
echo "    <!-- No specific interface -->"
echo ""
echo "Option 2: Specify interface explicitly (recommended for WSL2)"
echo "  <Domain id=\"any\">"
echo "    <General>"
echo "      <NetworkInterfaceAddress>$IFACE</NetworkInterfaceAddress>"
echo "    </General>"
echo ""
echo "Option 3: Try all interfaces"
echo "  <Domain id=\"any\">"
echo "    <General>"
echo "      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>"
echo "    </General>"
echo ""

# Test DDS with different interfaces
echo "=== DDS Interface Test ==="
echo ""

if [ ! -z "$IFACE" ]; then
    echo "Testing DDS with interface: $IFACE"
    echo "Command: ./build/bin/test_subscriber (will use $IFACE)"
    echo ""
    read -p "Run 5-second test? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml
        export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH
        
        echo "Testing for 5 seconds..."
        timeout 5 ./build/bin/test_subscriber 2>&1 | grep -i "received\|topic\|error" || echo "No messages received"
    fi
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Try running examples with explicit interface:"
echo "   ./build/bin/test_subscriber"
echo ""
echo "2. Check if robot is actually broadcasting DDS:"
echo "   sudo tcpdump -i $IFACE -n udp port 7400-7430 -v"
echo "   (Should see UDP packets if robot is broadcasting)"
echo ""
echo "3. Try the helloworld example between two terminals:"
echo "   Terminal 1: cd build/bin && ./publisher $IFACE"
echo "   Terminal 2: cd build/bin && ./subscriber $IFACE"
echo ""
echo "4. If still no luck, check:"
echo "   - Robot has SDK mode enabled in Unitree app"
echo "   - Robot firmware is up to date"
echo "   - Windows firewall isn't blocking UDP 7400-7430"
echo ""
