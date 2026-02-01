#!/bin/bash
echo "=== Checking for PATCHED message ==="
grep "PATCHED" all_msg.log | tail -5

echo ""
echo "=== New datachannel topics discovered ==="
grep "NEW DATACHANNEL" all_msg.log | tail -20

echo ""
echo "=== LIDAR/SLAM messages ==="
grep "LIDAR/SLAM MSG" all_msg.log | tail -20

echo ""
echo "=== All unique topics ==="
grep -oP '(?<=topic=)[^ ,]+' all_msg.log | sort -u

echo ""
echo "=== Message count ==="
grep -c "📨 \[" all_msg.log
