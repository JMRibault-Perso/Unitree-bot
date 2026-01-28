#!/bin/bash
# Scan for Unitree robot HTTP discovery endpoints

IPS="192.168.86.3 192.168.86.4 192.168.86.6 192.168.86.7 192.168.86.8 192.168.86.9 192.168.86.11 192.168.86.12 192.168.86.13 192.168.86.16"

# Common Unitree HTTP discovery endpoints
ENDPOINTS=(
    "/info"
    "/robot/info"
    "/api/info"
    "/api/robot"
    "/discovery"
    "/device/info"
)

PORTS="8080 8081 8082 9000 9991 18888 18889"

echo "Scanning for Unitree robot HTTP endpoints..."
echo

for IP in $IPS; do
    # Quick check if robot MAC
    MAC=$(arp -n $IP 2>/dev/null | grep -i 'fc:23:cd:92:60:02')
    if [ -n "$MAC" ]; then
        echo "✓ Found robot MAC at $IP!"
    fi
    
    for PORT in $PORTS; do
        for ENDPOINT in "${ENDPOINTS[@]}"; do
            RESPONSE=$(timeout 2 curl -s "http://$IP:$PORT$ENDPOINT" 2>/dev/null)
            if [ -n "$RESPONSE" ] && [ "$RESPONSE" != "404" ]; then
                echo "[$IP:$PORT$ENDPOINT] $RESPONSE"
            fi
        done
    done
done
