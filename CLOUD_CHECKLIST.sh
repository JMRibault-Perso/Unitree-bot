#!/bin/bash

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║  G1_6937 Cloud Connection Checklist                              ║
╚══════════════════════════════════════════════════════════════════╝

CURRENT STATUS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Robot bound to account (as G1_6937)
✓ Cloud authentication works (got token)
✗ Robot shows "Device not online" in cloud

CRITICAL: Check in Android App
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please check these in your Unitree Android app:

1. ROBOT ONLINE STATUS
   ──────────────────────────────────────────────────────────────
   Open app → Look at G1_6937
   
   Question: Does it show:
   [ ] Green dot / "Online" / "Connected"
   [ ] Gray dot / "Offline" / "Not Connected"
   [ ] Other status?

2. CONNECTION TYPE
   ──────────────────────────────────────────────────────────────
   When you tap on G1_6937 in the app:
   
   Question: Does it show:
   [ ] WiFi icon (direct local connection)
   [ ] Cloud icon (internet connection)
   [ ] Both?

3. ENABLE CLOUD/REMOTE ACCESS
   ──────────────────────────────────────────────────────────────
   In robot settings (⚙️ gear icon):
   
   Look for options like:
   [ ] "Remote Access" - Enable this
   [ ] "Cloud Control" - Enable this
   [ ] "Internet Connection" - Enable this
   [ ] "Allow API Access" - Enable this
   
   Enable ALL cloud-related options you find!

4. ROBOT MUST BE AWAKE
   ──────────────────────────────────────────────────────────────
   Question: Is the robot currently:
   [ ] Powered on and standing
   [ ] In sleep/standby mode
   [ ] Powered off
   
   For cloud to work, robot must be AWAKE and STANDING.

5. INTERNET CONNECTION
   ──────────────────────────────────────────────────────────────
   The robot itself needs internet access:
   
   Check in app:
   - WiFi status shows "Connected"
   - Internet connectivity indicator shows connected
   
   The robot must reach global-robot-api.unitree.com

TROUBLESHOOTING STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Wake Robot via App
──────────────────────────────────────────────────────────────────
If robot is in standby:
- Open Android app
- Tap G1_6937
- Tap "Wake Up" or "Power On"
- Wait for robot to stand up

Step 2: Enable Remote/Cloud Access
──────────────────────────────────────────────────────────────────
In app settings for G1_6937:
- Look for "Advanced" or "Developer" settings
- Enable "Remote Access" / "Cloud Control"
- Enable "API Access" if present

Step 3: Verify Internet Connection
──────────────────────────────────────────────────────────────────
In app, check:
- Robot WiFi shows connected
- Internet status shows online
- Cloud status shows connected

Step 4: Restart Robot (if needed)
──────────────────────────────────────────────────────────────────
If above doesn't work:
1. Power off robot completely
2. Wait 10 seconds
3. Power on
4. Wait for cloud connection
5. Try our script again

WHY "DEVICE NOT ONLINE":
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Device not online" from Unitree cloud means:

1. Robot is NOT actively connected to global-robot-api.unitree.com
2. Robot may be in sleep/standby mode
3. Cloud access may be disabled in settings
4. Robot's internet connection may be down

The Android app might work via LOCAL WiFi while cloud is offline.

DIFFERENCE: Local vs Cloud
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your Android app can connect TWO ways:

1. LOCAL (works now):
   App → WiFi → Robot (192.168.86.3)
   ✓ No internet needed
   ✓ Fast, low latency
   ✗ Only works on same WiFi

2. CLOUD (what we need):
   App → Internet → Unitree Cloud → Internet → Robot
   ✓ Works from anywhere
   ✗ Requires robot online to cloud
   ✗ Slightly higher latency

For Python SDK to work, robot MUST be cloud-connected.

AFTER ENABLING CLOUD ACCESS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Once robot shows "Online" in cloud:

1. Test connection:
   python3 test_g1_6937.py

2. If successful, run controller:
   python3 g1_webrtc_controller.py
   → Select Remote (option 3)
   → Use device name: G1_6937

3. Enjoy controlling your robot!

CURRENT CHECKLIST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please check and report back:

[ ] Robot status in app (Online/Offline)?
[ ] Any "Cloud" or "Remote Access" settings?
[ ] Is robot standing/awake or in standby?
[ ] Does app show internet/cloud connection?

Once we know this, we can fix the issue!

EOF
