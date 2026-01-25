#!/bin/bash

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║  Testing G1_6937 Connection with App Closed                      ║
╚══════════════════════════════════════════════════════════════════╝

IMPORTANT: Close the Android app before running this test!

WHY: The Android app may hold an exclusive WebRTC connection to the
robot. Only ONE WebRTC client can connect at a time.

STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Close Android App Completely
   ──────────────────────────────────────────────────────────────
   On your Android device:
   - Swipe up to show recent apps
   - Find Unitree app
   - Swipe it away to CLOSE (not just minimize)
   - Or: Settings → Apps → Unitree → Force Stop

2. Keep Robot Powered On
   ──────────────────────────────────────────────────────────────
   Robot should remain:
   - Powered on
   - Connected to WiFi
   - Standing or in ready mode

3. Run Test
   ──────────────────────────────────────────────────────────────
   Press Enter when ready...
EOF

read -p ""

echo ""
echo "Testing connection to G1_6937..."
echo ""

python3 test_g1_6937.py

if [ $? -eq 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ✓ SUCCESS! Connection works with app closed                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "RULE: Close Android app before using Python SDK"
    echo ""
    echo "Now you can run:"
    echo "  python3 g1_webrtc_controller.py"
    echo ""
else
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ✗ Still failing even with app closed                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "This means the robot is not connected to Unitree cloud."
    echo ""
    echo "Next steps:"
    echo "  1. Temporarily open Android app"
    echo "  2. Look for 'Cloud Mode' or 'Remote Access' setting"
    echo "  3. Enable it"
    echo "  4. Close app again"
    echo "  5. Re-run this test"
    echo ""
fi
