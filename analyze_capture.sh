#!/bin/bash
# Analyze robot boot capture to find connection protocol

PCAP_FILE="$1"

if [ -z "$PCAP_FILE" ]; then
    echo "Usage: $0 <capture.pcap>"
    exit 1
fi

if [ ! -f "$PCAP_FILE" ]; then
    echo "Error: File $PCAP_FILE not found"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "Analyzing: $PCAP_FILE"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Find robot IP
echo "1. Robot IP Detection"
echo "─────────────────────────────────────────────────────────────"
ROBOT_IP=$(tcpdump -r "$PCAP_FILE" -n 2>/dev/null | grep -oE '192\.168\.[0-9]+\.[0-9]+' | sort | uniq -c | sort -rn | head -5 | grep -v "$(hostname -I | awk '{print $1}')" | head -1 | awk '{print $2}')
echo "Robot IP: $ROBOT_IP"
echo ""

# Protocol breakdown
echo "2. Protocols Used"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "host $ROBOT_IP" 2>/dev/null | awk '{print $5}' | cut -d. -f5 | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
echo ""

# UDP ports
echo "3. UDP Ports (Robot → Phone)"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "src host $ROBOT_IP and udp" 2>/dev/null | grep -oE 'UDP.*length [0-9]+' | awk '{print $(NF-2), "bytes"}' | sort | uniq -c | sort -rn | head -10
echo ""

# TCP ports  
echo "4. TCP Ports"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "host $ROBOT_IP and tcp" 2>/dev/null | grep -oE '\.[0-9]+:' | tr -d '.:'| sort -u | head -20
echo ""

# DNS lookups
echo "5. DNS Queries from Robot"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "src host $ROBOT_IP and port 53" 2>/dev/null | grep -E "A\?|AAAA\?" | awk '{print $NF}' | sort -u
echo ""

# HTTP/HTTPS endpoints
echo "6. HTTP/HTTPS Connections"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "host $ROBOT_IP and (port 80 or port 443 or port 8080)" 2>/dev/null | head -20
echo ""

# First packets from robot after boot
echo "7. First 20 Packets from Robot (Boot Sequence)"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "src host $ROBOT_IP" 2>/dev/null | head -20
echo ""

# Broadcast/Multicast
echo "8. Broadcast/Multicast Packets (Discovery)"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "src host $ROBOT_IP and (broadcast or multicast)" 2>/dev/null | head -20
echo ""

# Extract unique UDP packet sizes
echo "9. UDP Packet Patterns"
echo "─────────────────────────────────────────────────────────────"
tcpdump -r "$PCAP_FILE" -n "src host $ROBOT_IP and udp" 2>/dev/null | awk '{print $NF}' | sort | uniq -c | sort -rn | head -10
echo ""

# Phone to robot traffic
echo "10. Phone → Robot Communication"
echo "─────────────────────────────────────────────────────────────"
PHONE_IP=$(tcpdump -r "$PCAP_FILE" -n "dst host $ROBOT_IP" 2>/dev/null | grep -oE 'IP [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | grep -v "$ROBOT_IP" | head -1 | awk '{print $2}')
echo "Phone IP: $PHONE_IP"
tcpdump -r "$PCAP_FILE" -n "src host $PHONE_IP and dst host $ROBOT_IP" 2>/dev/null | head -20
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "Key Findings Summary"
echo "═══════════════════════════════════════════════════════════════"
echo "Robot IP: $ROBOT_IP"
echo "Phone IP: $PHONE_IP"
echo ""
echo "To extract specific protocol data:"
echo "  # Save robot UDP stream"
echo "  tcpdump -r $PCAP_FILE -n 'src host $ROBOT_IP and udp' -w robot_udp.pcap"
echo ""
echo "  # Check for specific ports"
echo "  tcpdump -r $PCAP_FILE -n 'host $ROBOT_IP and port XXXX'"
echo "═══════════════════════════════════════════════════════════════"
