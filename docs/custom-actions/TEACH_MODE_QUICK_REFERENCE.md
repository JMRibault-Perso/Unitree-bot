# 🎬 Teach Mode Quick Reference Card

## Essential Endpoints

### Get Actions
```bash
# Get all actions (preset + custom)
GET /api/custom_action/robot_list

# Get saved favorites
GET /api/custom_action/list

# Get available gestures
GET /api/gestures/list
```

### Execute Actions ⭐ (Most Important)
```bash
# Play a custom action
POST /api/custom_action/execute?action_name=wave

# Stop custom action playback
POST /api/custom_action/stop
```

### Teaching Workflow
```bash
# 1. Start recording (API 7110)
POST /api/teach/record/start

# 2. [User manipulates robot for up to 20 seconds]

# 3. Stop recording (API 7110)
POST /api/teach/record/stop

# 4. Rename (optional)
POST /api/teach/rename
```

### Manage Favorites
```bash
# Add action to favorites
POST /api/custom_action/add?action_name=wave

# Remove from favorites
POST /api/custom_action/remove?action_name=wave
```

---

## JavaScript Examples

### Get and List Actions
```javascript
async function listActions() {
  const res = await fetch('/api/custom_action/robot_list');
  const data = await res.json();
  
  if (data.success) {
    console.log('Preset actions:', data.data.preset_actions);
    console.log('Custom actions:', data.data.custom_actions);
    
    // Display them
    data.data.custom_actions.forEach(action => {
      console.log(`- ${action.name} (${action.duration}ms)`);
    });
  }
}
```

### Execute Custom Action
```javascript
async function playCustomAction(actionName) {
  const res = await fetch(`/api/custom_action/execute?action_name=${actionName}`, {
    method: 'POST'
  });
  const data = await res.json();
  
  if (data.success) {
    console.log(`Playing: ${actionName}`);
  } else {
    console.error('Error:', data.error);
  }
}

// Usage
playCustomAction('wave');
```

### Full Teaching Workflow
```javascript
async function teachNewAction(actionName) {
  try {
    // Step 1: Start recording
    console.log('Starting record...');
    const startRes = await fetch('/api/teach/record/start', { method: 'POST' });
    const startData = await startRes.json();
    const createdName = startData.action_name;
    
    // Step 2: Wait for user input
    console.log('Recording... (user moves robot)');
    await new Promise(resolve => setTimeout(resolve, 5000)); // demo duration
    
    // Step 3: Stop recording
    console.log('Stopping record...');
    await fetch('/api/teach/record/stop', { method: 'POST' });
    
    // Step 4: Rename (optional)
    console.log(`Renaming to "${actionName}"...`);
    await fetch('/api/teach/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_name: createdName, new_name: actionName })
    });
    
    console.log('✅ Teaching complete!');
  } catch (err) {
    console.error('Teaching failed:', err);
  }
}

// Usage
teachNewAction('my_wave');
```

### Real-time Status Updates (WebSocket)
```javascript
function connectStatusUpdates() {
  const ws = new WebSocket('ws://localhost:9000/ws');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'connection_status') {
      console.log('Connection:', data.connected ? '✅' : '❌');
    }
    
    if (data.type === 'fsm_state') {
      console.log('FSM State:', data.fsm_id);
    }
    
    if (data.type === 'battery') {
      console.log('Battery:', data.voltage, 'V');
    }
  };
  
  ws.onerror = (err) => console.error('WebSocket error:', err);
}
```

---

## Python Examples

### Using requests library
```python
import requests
import json

BASE_URL = 'http://localhost:9000'

# Get all actions
def get_actions():
    res = requests.get(f'{BASE_URL}/api/custom_action/robot_list')
    data = res.json()
    return data['data']['custom_actions']

# Execute custom action
def play_action(action_name):
    res = requests.post(
        f'{BASE_URL}/api/custom_action/execute',
        params={'action_name': action_name}
    )
    return res.json()

# List and play
if __name__ == '__main__':
    actions = get_actions()
    for action in actions:
        print(f"- {action['name']}")
    
    if actions:
        result = play_action(actions[0]['name'])
        print(f"Played: {result}")
```

### Using asyncio
```python
import aiohttp
import asyncio

BASE_URL = 'http://localhost:9000'

async def get_actions():
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{BASE_URL}/api/custom_action/robot_list') as res:
            data = await res.json()
            return data['data']['custom_actions']

async def play_action(action_name):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'{BASE_URL}/api/custom_action/execute',
            params={'action_name': action_name}
        ) as res:
            return await res.json()

async def main():
    actions = await get_actions()
    for action in actions:
        print(f"- {action['name']}")
    
    if actions:
        result = await play_action(actions[0]['name'])
        print(f"Result: {result}")

asyncio.run(main())
```

---

## Key Points to Remember

### ✅ Do's
- ✅ Check connection status before executing actions
- ✅ Use API 7110 to start/stop recording
- ✅ Use exact action name when executing (case-sensitive!)
- ✅ Follow the UI prompts for record/save/playback

### ❌ Don'ts
- ❌ Don't force FSM state transitions (robot may fall)
- ❌ Don't interrupt recording mid-action
- ❌ Don't execute actions while recording
- ✅ Check the action list before use
- ❌ Don't record actions without entering teach mode first

---

## Common Responses

### Success Response
```json
{
  "success": true,
  "action": "wave",
  "message": "Custom action queued for playback"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Action 'unknown_action' not found"
}
```

### Action List Response
```json
{
  "success": true,
  "data": {
    "preset_actions": [
      {"id": 99, "name": "release arm", "duration": 0},
      {"id": 18, "name": "high five", "duration": 2000}
    ],
    "custom_actions": [
      {"name": "wave custom", "duration": 3500},
      {"name": "bow", "duration": 1200}
    ]
  }
}
```

---

## Full Web Interface

### Main Dashboard
**URL:** `http://localhost:9000`
- Shows connection status
- Lists quick actions
- Expandable teach mode panel
- Link to full interface

### Full Teach Mode Page
**URL:** `http://localhost:9000/teach`
- Complete workflow UI
- Action library with search
- Recording interface
- Real-time status updates
- Emergency controls

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Not connected" | Check WebRTC on main page, verify robot WiFi |
| "Action not found" | Get list first, use exact name (case-sensitive) |
| Recording doesn't work | Start recording again (API 7110) and keep the robot connected |
| Favorites don't save | Check browser storage permissions |
| API returns error 7404 | Robot not in correct mode (500/501, or 801 with mode 0/3 for playback) |

---

## API Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | All good! |
| 400 | Bad Request | Check parameter format |
| 404 | Not Found | Action or endpoint doesn't exist |
| 500 | Server Error | Check web server logs |
| 7400 | Arm Occupied | Another command in progress |
| 7401 | Arm Raised | Arm in raised position |
| 7404 | Invalid FSM | Robot not in correct mode |

---

## Environment Setup

### Start Web Server
```bash
cd c:\Unitree\G1\Unitree-bot
cd g1_app
python -m uvicorn ui.web_server:app --host 0.0.0.0 --port 9000 --reload
```

### Access Interface
```
http://localhost:9000/teach
```

### Connect to Robot
1. Robot must be on same WiFi network
2. Check IP in Android app or router
3. WebRTC connection should establish automatically
4. Wait for "Connected" status on page

---

**Ready to teach your robot! 🎬**

For more details, see [TEACH_MODE_IMPLEMENTATION_STATUS.md](TEACH_MODE_IMPLEMENTATION_STATUS.md)
