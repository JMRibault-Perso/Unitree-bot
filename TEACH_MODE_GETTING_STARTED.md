# 🚀 Getting Started with Teach Mode

## ⚡ Quick Start (60 seconds)

### Step 1: Start Web Server
```bash
cd c:\Unitree\G1\Unitree-bot
cd g1_app
python -m uvicorn ui.web_server:app --host 0.0.0.0 --port 9000 --reload
```

### Step 2: Open Browser
```
http://localhost:9000
```

### Step 3: Access Teach Mode
Option A: From main dashboard
- Scroll to "🎬 Custom Actions (Teach Mode)" section
- Click "Open Full Teach Mode Interface"

Option B: Direct URL
```
http://localhost:9000/teach
```

### Step 4: Check Connection
- You should see a green "✅ Connected" status badge
- If not, check that robot is on same WiFi network

### Step 5: Choose Your Action
- **Option 1:** Execute existing custom action
  - Look in "Action Library" section
  - Click play button next to action name
  
- **Option 2:** Record new custom action
  - Follow the 6-step workflow on the page
  - Click "Enter Damping Mode" to start

---

## 🎬 Three Ways to Teach the Robot

### Method 1: Execute Existing Custom Action (5 seconds)
**Use this if:** You already have custom actions recorded (via Android app)

1. Go to http://localhost:9000/teach
2. Find action in "Action Library"
3. Click ▶️ play button
4. Robot executes action
5. Done! ✅

**Browser Console Test:**
```javascript
fetch('/api/custom_action/execute?action_name=wave', {
  method: 'POST'
}).then(r => r.json()).then(data => console.log(data));
```

---

### Method 2: Record from Web Interface (5 minutes)
**Use this if:** You want to record a new action via web controller

1. **Prepare:** Go to http://localhost:9000/teach
   - Verify "Connected" status
   - Robot in safe position

2. **Enter Teach Mode**
   - Click "🎭 Enter Damping Mode" button
   - Wait for confirmation message
   - Robot enters **special zero-gravity compensation mode** (command 0x0D)
   - Upper body arms become gravity-compensated (compliant, lightweight)
   - Lower body automatically maintains balance

3. **Start Recording**
   - Click "🔴 Start Record" button
   - Page will show "Recording in progress..."

4. **Move Robot** (3-5 seconds)
   - Manually move robot arm/body
   - Create the action you want to teach
   - Be smooth and deliberate

5. **Stop Recording**
   - Click "⏹️ Stop Record" button
   - Recording stops

6. **Save Recording**
   - Enter action name (e.g., "wave hand", "bow")
   - Click "💾 Save Recording" button
   - Wait for confirmation

7. **Test Playback** (optional)
   - Click "▶️ Play Action" button
   - Robot should repeat the recorded action

8. **Exit Teaching**
   - Click "🎭 Exit Damping Mode" button
   - Robot returns to normal control

**Step-by-Step Flow:**
```
STEP 1: Enter Damping Mode
        Robot goes to zero-torque (FSM 501)
        ↓
STEP 2: Start Recording
        Recording engine initialized
        ↓
STEP 3: User Moves Robot
        You manually manipulate robot (3-5 sec)
        ↓
STEP 4: Stop Recording
        Recording saved in memory
        ↓
STEP 5: Save Recording
        Recording stored with name
        ↓
STEP 6: Test/Play
        Verify the action works
        ↓
STEP 7: Exit Damping Mode
        Robot returns to normal control
```

---

### Method 3: Via HTTP API (Programmers)
**Use this if:** You want to automate teaching via code

**JavaScript:**
```javascript
// Get all actions
async function listActions() {
  const res = await fetch('/api/custom_action/robot_list');
  const data = await res.json();
  console.log(data.data.custom_actions);
}

// Execute action
async function playAction(name) {
  await fetch(`/api/custom_action/execute?action_name=${name}`, {
    method: 'POST'
  });
}

// Full workflow
async function recordNewAction(actionName) {
  // Enter teaching
  await fetch('/api/teaching/enter_damping', { method: 'POST' });
  
  // Start recording
  await fetch('/api/teaching/start_record', { method: 'POST' });
  
  // Wait for user to move robot
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // Stop recording
  await fetch('/api/teaching/stop_record', { method: 'POST' });
  
  // Save
  await fetch(`/api/teaching/save?action_name=${actionName}&duration=5000`, {
    method: 'POST'
  });
  
  // Exit
  await fetch('/api/teaching/exit_damping', { method: 'POST' });
}

// Usage
listActions();
playAction('wave');
recordNewAction('my_custom_action');
```

**Python:**
```python
import requests
import time
import asyncio

BASE = 'http://localhost:9000'

# List actions
def list_actions():
    r = requests.get(f'{BASE}/api/custom_action/robot_list')
    return r.json()['data']['custom_actions']

# Execute action
def play_action(name):
    r = requests.post(f'{BASE}/api/custom_action/execute', 
                     params={'action_name': name})
    return r.json()

# Record workflow
def record_action(name, duration=5):
    # Enter teaching
    requests.post(f'{BASE}/api/teaching/enter_damping')
    time.sleep(1)
    
    # Start record
    requests.post(f'{BASE}/api/teaching/start_record')
    
    # Wait for manual input
    print(f"Move robot for {duration} seconds...")
    time.sleep(duration)
    
    # Stop record
    requests.post(f'{BASE}/api/teaching/stop_record')
    time.sleep(1)
    
    # Save
    requests.post(f'{BASE}/api/teaching/save',
                 params={'action_name': name, 'duration': duration*1000})
    time.sleep(1)
    
    # Exit
    requests.post(f'{BASE}/api/teaching/exit_damping')
    
    print(f"✅ Saved action: {name}")

# Usage
if __name__ == '__main__':
    # List actions
    actions = list_actions()
    print(f"Found {len(actions)} actions")
    
    # Play first action
    if actions:
        play_action(actions[0]['name'])
    
    # Record new
    record_action('my_wave')
```

**cURL (Terminal):**
```bash
# List actions
curl http://localhost:9000/api/custom_action/robot_list

# Execute action
curl -X POST "http://localhost:9000/api/custom_action/execute?action_name=wave"

# Enter teaching
curl -X POST http://localhost:9000/api/teaching/enter_damping

# Start record
curl -X POST http://localhost:9000/api/teaching/start_record

# Stop record
curl -X POST http://localhost:9000/api/teaching/stop_record

# Save recording
curl -X POST "http://localhost:9000/api/teaching/save?action_name=mywave&duration=5000"

# Play back
curl -X POST "http://localhost:9000/api/teaching/play?action_id=1"

# Exit teaching
curl -X POST http://localhost:9000/api/teaching/exit_damping
```

---

## 🐛 Troubleshooting

### Issue: "Not connected" Status

**Symptoms:**
- Red "❌ Not connected" badge
- Can't execute actions
- "Not connected" error messages

**Solutions:**
1. Check WebRTC connection on main dashboard first
   - Go to http://localhost:9000
   - Should see green indicator at top

2. Verify robot is on WiFi
   - Check Android app or router
   - Note robot's IP address

3. Check network connectivity
   - Can you ping the robot?
   - `ping 192.168.86.3` (replace with your robot IP)

4. Restart web server
   ```bash
   # Stop current server (Ctrl+C)
   # Restart:
   python -m uvicorn ui.web_server:app --host 0.0.0.0 --port 9000
   ```

5. Check browser console for errors
   - Press F12 in browser
   - Click "Console" tab
   - Look for red error messages

---

### Issue: "Action Not Found"

**Symptoms:**
- "Action 'wave' not found" error
- Custom action won't execute

**Solutions:**
1. Get the exact action name
   ```bash
   curl http://localhost:9000/api/custom_action/robot_list
   # Copy exact name from response (case-sensitive!)
   ```

2. Verify action exists on robot
   - Use Android app to confirm action is saved
   - Check action name matches exactly (case-sensitive)

3. Use exact name in request
   ```bash
   # Case matters!
   curl -X POST "http://localhost:9000/api/custom_action/execute?action_name=Wave"  # ❌ Won't work if saved as "wave"
   curl -X POST "http://localhost:9000/api/custom_action/execute?action_name=wave"   # ✅ Correct
   ```

---

### Issue: Recording Won't Save

**Symptoms:**
- Started recording, moved robot, but save failed
- "Failed to save action" error

**Solutions:**
1. Verify you entered teach mode first
   - Must click "Enter Damping Mode" before "Start Record"
   - Should see message that damping mode entered

2. Check action name is not empty
   - When saving, must provide action name
   - Name cannot be blank

3. Verify recording actually started
   - Page should show "Recording in progress..."
   - Time counter should increment

4. Check robot is in correct teaching mode
   - Robot should be in **zero-gravity compensation mode** (entered via command 0x0D)
   - This is **NOT** FSM 1 (DAMP) - it's a special gravity-compensated teaching mode
   - Arms should feel light and gravity-compensated when manipulated
   - Legs should maintain automatic balance
   - If mode is wrong, click "Exit Damping Mode" then "Enter Damping Mode" again

5. Look for detailed error in browser console
   - Press F12 → Console
   - Look for error message details

---

### Issue: Robot Doesn't Move on Playback

**Symptoms:**
- Click play button, nothing happens
- No error message

**Solutions:**
1. Verify robot is ready
   - Not in teach/damp mode
   - Click "Exit Damping Mode" if needed

2. Check FSM state
   - Robot must be in appropriate state for action
   - Usually needs to be in normal mode (FSM 500)

3. Verify action exists
   - List all actions: `curl http://localhost:9000/api/custom_action/robot_list`
   - Confirm action is in the list

4. Check web server logs
   - Look at terminal running web server
   - Should see POST request log
   - Look for error messages

5. Restart robot connection
   - Go to main dashboard
   - Disconnect and reconnect

---

## 📊 Status Indicators

### Connection Badge
| Badge | Meaning | Action |
|-------|---------|--------|
| 🟢 Connected | Ready to use | Proceed normally |
| 🔴 Not Connected | Can't reach robot | Check WiFi, restart server |
| 🟠 Recording | Currently recording | Wait or click Stop |
| 🟡 Damping Mode | In teach mode | Click Exit when done |

### Status Messages
```
✅ Recording started
❌ Failed to connect
⏳ Connecting...
🎬 Action playing
📌 Action saved
🛑 Recording stopped
```

---

## ⌚ Timing Guide

| Operation | Time | Notes |
|-----------|------|-------|
| List actions | ~200ms | Network dependent |
| Execute action | ~100ms | Send time only |
| Enter teaching | ~500ms | FSM transition |
| Start recording | ~100ms | Begin capture |
| Record action | 3-5s | User time |
| Stop recording | ~100ms | End capture |
| Save action | ~1s | Transmission |
| Play action | ~2-5s | Depends on action |
| Exit teaching | ~500ms | FSM transition |

---

## 🎯 Common Workflows

### Workflow 1: Quick Test Existing Action
```
1. Open http://localhost:9000/teach
2. Find action in library
3. Click play button
4. Wait 3-5 seconds
5. Action complete!
Time: ~10 seconds
```

### Workflow 2: Record Simple Gesture
```
1. Open http://localhost:9000/teach
2. Click "Enter Damping Mode"
3. Click "Start Record"
4. Move arm up and down (3 sec)
5. Click "Stop Record"
6. Type "wave"
7. Click "Save Recording"
8. Click "Play Action" (optional)
9. Click "Exit Damping Mode"
Time: ~5 minutes
```

### Workflow 3: Record Complex Movement
```
1. Open http://localhost:9000/teach
2. Click "Enter Damping Mode"
3. Click "Start Record"
4. Move entire body (walk, turn, gesture) - 5-10 seconds
5. Click "Stop Record"
6. Type "dance"
7. Click "Save Recording"
8. Click "Play Action"
9. Click "Exit Damping Mode"
Time: ~10 minutes
```

### Workflow 4: Automation (Python Script)
```python
# See Method 3: Via HTTP API above
# Can automate entire teaching workflow
Time: < 10 seconds per action (user moves robot manually)
```

---

## 📱 Mobile Access

### From Mobile Browser
```
http://<PC-IP>:9000
# Example:
http://192.168.1.100:9000
```

### Find Your PC IP
**Windows (PowerShell):**
```powershell
ipconfig
# Look for "IPv4 Address" under your network adapter
```

**macOS/Linux (Terminal):**
```bash
ifconfig
# Look for "inet" address under your network interface
```

### Mobile Workflow
1. Find PC IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
2. Open http://<PC-IP>:9000 in mobile browser
3. Same workflow as desktop (might be easier to hold robot!)

---

## ✅ Pre-Flight Checklist

Before starting teach mode:

- [ ] Web server is running on port 9000
- [ ] Robot is powered on and on WiFi
- [ ] Browser shows "Connected" status
- [ ] You can reach http://localhost:9000
- [ ] Robot is in safe position (not at edge of table)
- [ ] You have space to move robot arm
- [ ] No obstacles around robot
- [ ] Someone can stop robot if needed (safety partner recommended)

---

## 🚨 Safety Reminders

### Important Safety Notes
1. **Teach mode = zero-torque**
   - Robot arm will fall if not supported
   - Support the arm while moving it
   - Don't let it swing freely

2. **Exit teaching before normal operation**
   - Always click "Exit Damping Mode"
   - Robot won't respond properly if still in damp mode

3. **Watch the robot**
   - Don't leave robot unattended while teaching
   - Watch playback first time (might be unexpected)

4. **Emergency stop available**
   - Red stop button always on interface
   - Can also unplug robot if needed

5. **Not recommended for new users without supervision**
   - First time should be with someone experienced
   - Start with simple arm movements
   - Graduate to full body movements

---

## 🎓 Learning Path

### Beginner
1. Start with executing existing custom actions (Method 1)
2. Watch a few actions to understand behavior
3. Try simple teach mode recording (1-2 second movements)

### Intermediate  
1. Record more complex movements (5-10 seconds)
2. Create action sequences (multiple teaches)
3. Use web API (JavaScript/Python)

### Advanced
1. Automate teaching via Python scripts
2. Create complex gesture sequences
3. Export/import actions
4. Modify actions programmatically

---

## 📞 Quick Reference

**Access Teach Mode:**
- Main dashboard: http://localhost:9000
- Direct access: http://localhost:9000/teach
- API endpoint: POST /api/custom_action/execute

**Quick API calls:**
```bash
# List actions
curl http://localhost:9000/api/custom_action/robot_list

# Execute action
curl -X POST "http://localhost:9000/api/custom_action/execute?action_name=wave"

# Full workflow: See Method 3 section above
```

**Troubleshooting:**
- Not connected? → Check WiFi and WebRTC connection
- Action not found? → Get exact name from action list
- Recording won't save? → Enter damping mode first

**Need help?**
- Check browser console (F12) for error messages
- Look at web server logs for details
- See troubleshooting section above

---

**Ready to teach your robot? Let's go! 🚀**

For more details, see:
- [TEACH_MODE_IMPLEMENTATION_STATUS.md](TEACH_MODE_IMPLEMENTATION_STATUS.md) - Complete feature audit
- [TEACH_MODE_QUICK_REFERENCE.md](TEACH_MODE_QUICK_REFERENCE.md) - API reference
- [TEACH_MODE_SUMMARY.md](TEACH_MODE_SUMMARY.md) - Technical summary
