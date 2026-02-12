# UI Improvement - Implementation Code Snippets

## 1. Network Mode Selector (HTML)

**Add to connection modal (replace current form):**

```html
<div id="connectionModal" class="modal">
    <div class="modal-content">
        <div class="modal-title">Connect to Robot</div>
        
        <!-- Network Mode Selection -->
        <div class="form-group">
            <label class="form-label">Connection Method</label>
            <div class="radio-group">
                <label class="radio-option">
                    <input type="radio" name="connectionMode" value="sta" checked onchange="updateConnectionMode()">
                    <div class="radio-label">
                        <strong>Home WiFi Network</strong>
                        <span class="radio-description">Robot is on same WiFi as this computer</span>
                    </div>
                </label>
                <label class="radio-option">
                    <input type="radio" name="connectionMode" value="ap" onchange="updateConnectionMode()">
                    <div class="radio-label">
                        <strong>Direct Connection (AP Mode)</strong>
                        <span class="radio-description">Connect to robot's WiFi "G1_6937"</span>
                    </div>
                </label>
            </div>
        </div>

        <!-- STA Mode: Robot Selection -->
        <div id="staMode" class="form-group">
            <label class="form-label">Select Robot</label>
            <select id="robotSelect" class="form-input" onchange="selectRobot()">
                <option value="">-- Choose a robot --</option>
            </select>
            <div class="help-text">Don't see your robot? <a href="#" onclick="scanNetwork()">Scan network</a></div>
        </div>

        <!-- AP Mode: WiFi Check -->
        <div id="apMode" class="form-group" style="display: none;">
            <div class="info-box">
                <strong>ℹ️ AP Mode Connection</strong>
                <ol>
                    <li>Connect your computer to WiFi: <code id="apWifiName">G1_6937</code></li>
                    <li>Robot IP address: <code>192.168.12.1</code> (fixed)</li>
                </ol>
                <div id="wifiStatus" class="status-indicator">
                    <span class="status-dot"></span>
                    <span id="wifiStatusText">Checking WiFi connection...</span>
                </div>
            </div>
        </div>

        <!-- Discovery Progress (only shown during scan) -->
        <div id="discoveryProgress" class="discovery-progress" style="display: none;">
            <div class="progress-header">🔍 Searching for robot...</div>
            <ul class="progress-steps">
                <li id="step-multicast" class="pending">Trying multicast discovery...</li>
                <li id="step-ap" class="pending">Checking AP mode (192.168.12.1)...</li>
                <li id="step-arp" class="pending">Scanning network...</li>
            </ul>
        </div>

        <!-- Serial Number (only shown for new robots) -->
        <div id="serialNumberGroup" class="form-group" style="display: none;">
            <label class="form-label">
                Serial Number
                <span class="help-icon" title="Found on robot label or in Unitree app">?</span>
            </label>
            <input type="text" id="robotSerial" class="form-input" placeholder="e.g., E21D1000PAHBMB06">
        </div>

        <!-- Action Buttons -->
        <div class="form-buttons">
            <button class="btn-primary" id="connectBtn" onclick="connectRobot()">
                <span id="connectBtnText">Connect to Robot</span>
            </button>
            <button class="btn-secondary" onclick="closeConnectionModal()">Cancel</button>
        </div>

        <!-- Advanced Options (collapsed) -->
        <details class="advanced-options">
            <summary>Advanced Options</summary>
            <div class="form-group">
                <label class="form-label">Manual IP Override</label>
                <input type="text" id="manualIp" class="form-input" placeholder="e.g., 192.168.1.100">
            </div>
        </details>
    </div>
</div>
```

## 2. CSS Styles

```css
/* Radio Group Styling */
.radio-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.radio-option {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.radio-option:hover {
    border-color: var(--primary);
    background: rgba(102, 126, 234, 0.05);
}

.radio-option input[type="radio"]:checked + .radio-label {
    color: var(--primary);
}

.radio-label {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.radio-description {
    font-size: 12px;
    color: var(--text-muted);
}

/* Info Box (AP Mode Instructions) */
.info-box {
    background: rgba(102, 126, 234, 0.1);
    border: 1px solid var(--primary);
    border-radius: 8px;
    padding: 15px;
    font-size: 13px;
}

.info-box code {
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    color: var(--primary);
}

.info-box ol {
    margin: 10px 0 10px 20px;
}

/* Status Indicator */
.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    padding: 8px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
}

.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--text-muted);
}

.status-indicator.online .status-dot {
    background: var(--success);
    animation: pulse 2s infinite;
}

.status-indicator.offline .status-dot {
    background: var(--danger);
}

/* Discovery Progress */
.discovery-progress {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
}

.progress-header {
    font-weight: 600;
    margin-bottom: 10px;
}

.progress-steps {
    list-style: none;
    padding: 0;
}

.progress-steps li {
    padding: 8px 0 8px 30px;
    position: relative;
    color: var(--text-muted);
    font-size: 13px;
}

.progress-steps li::before {
    content: '⏱️';
    position: absolute;
    left: 0;
}

.progress-steps li.active {
    color: var(--primary);
    font-weight: 500;
}

.progress-steps li.active::before {
    content: '🔄';
    animation: spin 1s linear infinite;
}

.progress-steps li.complete::before {
    content: '✅';
}

.progress-steps li.failed::before {
    content: '❌';
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Help Text and Icons */
.help-text {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 5px;
}

.help-text a {
    color: var(--primary);
    text-decoration: none;
}

.help-text a:hover {
    text-decoration: underline;
}

.help-icon {
    display: inline-block;
    width: 16px;
    height: 16px;
    background: var(--primary);
    color: white;
    border-radius: 50%;
    text-align: center;
    font-size: 11px;
    line-height: 16px;
    cursor: help;
    margin-left: 5px;
}

/* Advanced Options */
.advanced-options {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.advanced-options summary {
    cursor: pointer;
    color: var(--text-muted);
    font-size: 12px;
    user-select: none;
}

.advanced-options summary:hover {
    color: var(--primary);
}

/* Button States */
.btn-primary.loading {
    opacity: 0.7;
    pointer-events: none;
}

.btn-primary.loading::after {
    content: '';
    width: 14px;
    height: 14px;
    margin-left: 8px;
    border: 2px solid white;
    border-top-color: transparent;
    border-radius: 50%;
    display: inline-block;
    animation: spin 0.6s linear infinite;
}
```

## 3. JavaScript Functions

```javascript
// Connection mode switching
function updateConnectionMode() {
    const mode = document.querySelector('input[name="connectionMode"]:checked').value;
    
    if (mode === 'ap') {
        document.getElementById('staMode').style.display = 'none';
        document.getElementById('apMode').style.display = 'block';
        
        // Check current WiFi status
        checkAPModeStatus();
    } else {
        document.getElementById('staMode').style.display = 'block';
        document.getElementById('apMode').style.display = 'none';
    }
}

// Check if computer is connected to robot's AP WiFi
async function checkAPModeStatus() {
    try {
        const response = await fetch('/api/wifi/current');
        const data = await response.json();
        
        const wifiStatus = document.getElementById('wifiStatus');
        const wifiStatusText = document.getElementById('wifiStatusText');
        
        if (data.ssid && data.ssid.includes('G1_')) {
            wifiStatus.classList.add('online');
            wifiStatus.classList.remove('offline');
            wifiStatusText.textContent = `✓ Connected to ${data.ssid}`;
            
            // Update AP WiFi name dynamically
            document.getElementById('apWifiName').textContent = data.ssid;
        } else {
            wifiStatus.classList.add('offline');
            wifiStatus.classList.remove('online');
            wifiStatusText.textContent = `✗ Not connected to robot WiFi. Current: ${data.ssid || 'Unknown'}`;
        }
    } catch (e) {
        console.error('Failed to check WiFi status:', e);
    }
}

// Network scan with progress
async function scanNetwork() {
    const progressDiv = document.getElementById('discoveryProgress');
    progressDiv.style.display = 'block';
    
    const steps = ['multicast', 'ap', 'arp'];
    let currentStep = 0;
    
    // Animate progress
    const stepInterval = setInterval(() => {
        if (currentStep > 0) {
            document.getElementById(`step-${steps[currentStep - 1]}`)?.classList.remove('active');
        }
        if (currentStep < steps.length) {
            document.getElementById(`step-${steps[currentStep]}`)?.classList.add('active');
            currentStep++;
        }
    }, 1000);
    
    try {
        const mac = document.getElementById('robotSelect').value || G1_MAC;
        const response = await fetch(`/api/discover?mac=${mac}`);
        const data = await response.json();
        
        clearInterval(stepInterval);
        
        if (data.ip) {
            // Mark all steps complete
            steps.forEach(step => {
                document.getElementById(`step-${step}`)?.classList.remove('active');
                document.getElementById(`step-${step}`)?.classList.add('complete');
            });
            
            // Show success message
            setTimeout(() => {
                progressDiv.style.display = 'none';
                alert(`✅ Robot found at ${data.ip}`);
                
                // Auto-populate robot selection
                // (implementation depends on your robot list structure)
            }, 1000);
        } else {
            // Mark as failed
            document.getElementById(`step-${steps[currentStep - 1]}`)?.classList.add('failed');
            showDiscoveryError();
        }
    } catch (e) {
        clearInterval(stepInterval);
        showDiscoveryError(e.message);
    }
}

function showDiscoveryError(message = '') {
    const progressDiv = document.getElementById('discoveryProgress');
    progressDiv.innerHTML = `
        <div class="error-box">
            <strong>❌ Robot not found</strong>
            <p>${message}</p>
            <p><strong>Troubleshooting:</strong></p>
            <ul>
                <li>Is the robot powered on?</li>
                <li>Are you connected to the same WiFi network?</li>
                <li>Try connecting to robot's WiFi "G1_6937" (AP mode)</li>
            </ul>
            <button class="btn-secondary" onclick="document.getElementById('discoveryProgress').style.display='none'">
                Close
            </button>
        </div>
    `;
}

// Enhanced connection function
async function connectRobot() {
    const connectBtn = document.getElementById('connectBtn');
    const connectBtnText = document.getElementById('connectBtnText');
    const mode = document.querySelector('input[name="connectionMode"]:checked').value;
    
    // Update button state
    connectBtn.classList.add('loading');
    connectBtn.disabled = true;
    connectBtnText.textContent = 'Connecting...';
    
    try {
        let robotIp;
        let robotMac;
        let serialNumber;
        
        if (mode === 'ap') {
            // AP Mode: Use fixed IP
            robotIp = '192.168.12.1';
            robotMac = G1_MAC; // Default, or get from selection
            serialNumber = G1_SERIAL; // Or prompt if unknown
            
        } else {
            // STA Mode: Discover IP
            const selectedRobot = document.getElementById('robotSelect').value;
            if (!selectedRobot) {
                throw new Error('Please select a robot');
            }
            
            const robot = allRobots.find(r => r.mac === selectedRobot);
            
            // Check for manual IP override
            const manualIp = document.getElementById('manualIp')?.value;
            if (manualIp) {
                robotIp = manualIp;
            } else {
                // Trigger discovery with progress
                await scanNetwork();
                // Get discovered IP (you'll need to store this from scanNetwork)
                robotIp = robot.ip;
            }
            
            robotMac = robot.mac;
            serialNumber = robot.serial_number;
        }
        
        // Make connection request
        const response = await fetch(`/api/connect?ip=${robotIp}&mac=${robotMac}&serial_number=${serialNumber}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            connectedRobotMac = robotMac;
            currentRobot = { mac: robotMac, serial_number: serialNumber, ip: robotIp };
            document.getElementById('robotName').textContent = allRobots.find(r => r.mac === robotMac)?.nickname || 'G1 Robot';
            closeConnectionModal();
            updateConnectionStatus(true);
            startVideoStream();
            startPointCloudPolling();
            
            // Update button back to disconnect state
            connectBtnText.textContent = 'Disconnect';
            connectBtn.classList.remove('loading');
            connectBtn.classList.add('connected');
            connectBtn.onclick = disconnectRobot;
            
        } else {
            throw new Error(data.error || 'Connection failed');
        }
        
    } catch (e) {
        // Show user-friendly error
        alert(`Connection failed: ${e.message}\n\nTroubleshooting:\n• Check robot is powered on\n• Verify WiFi connection\n• Try AP mode if on different network`);
        
        // Reset button
        connectBtn.classList.remove('loading');
        connectBtn.disabled = false;
        connectBtnText.textContent = 'Connect to Robot';
    }
}
```

## 4. Backend API Endpoints

**Add to `web_server.py`:**

```python
@app.get("/api/wifi/current")
async def get_current_wifi():
    """Get current WiFi network SSID"""
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.split('\n'):
                if line.startswith('yes:'):
                    ssid = line.split(':')[1]
                    is_ap = 'G1_' in ssid
                    return {"ssid": ssid, "is_ap_mode": is_ap}
        
        elif platform.system() == "Windows":
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.split('\n'):
                if 'SSID' in line and 'BSSID' not in line:
                    ssid = line.split(':')[1].strip()
                    is_ap = 'G1_' in ssid
                    return {"ssid": ssid, "is_ap_mode": is_ap}
        
        return {"ssid": None, "is_ap_mode": False}
        
    except Exception as e:
        logger.error(f"Failed to get WiFi SSID: {e}")
        return {"ssid": None, "is_ap_mode": False, "error": str(e)}


@app.get("/api/network/mode")
async def detect_network_mode(mac: str = G1_MAC):
    """Detect if robot is in AP or STA mode and return connection info"""
    try:
        from g1_app.utils.arp_discovery import G1_AP_IP, ping_test, discover_robot_ip
        
        # Check if AP mode is available (robot at 192.168.12.1)
        ap_available = ping_test(G1_AP_IP, timeout=1)
        
        if ap_available:
            return {
                "mode": "AP",
                "ip": G1_AP_IP,
                "available": True,
                "wifi_name": f"G1_{mac[-4:]}",  # e.g., G1_6937
                "message": f"Robot is in AP mode. Connect to WiFi 'G1_{mac[-4:]}'"
            }
        else:
            # Try discovery on local network
            discovered_ip = discover_robot_ip(target_mac=mac, fast=True)
            
            if discovered_ip:
                return {
                    "mode": "STA",
                    "ip": discovered_ip,
                    "available": True,
                    "message": f"Robot found on local network at {discovered_ip}"
                }
            else:
                return {
                    "mode": "UNKNOWN",
                    "ip": None,
                    "available": False,
                    "message": "Robot not found. Check power and WiFi connection."
                }
    
    except Exception as e:
        logger.error(f"Network mode detection failed: {e}")
        return {
            "mode": "ERROR",
            "ip": None,
            "available": False,
            "error": str(e)
        }


@app.post("/api/connect")
async def connect_robot(
    mac: str,
    serial_number: str,
    ip: Optional[str] = None,
    mode: str = "auto"  # "auto", "sta", or "ap"
):
    """
    Enhanced connection endpoint with AP mode support
    
    Args:
        mac: Robot MAC address
        serial_number: Robot serial number
        ip: Optional manual IP override
        mode: Connection mode (auto/sta/ap)
    """
    global robot
    
    try:
        async with connect_lock:
            # Determine IP based on mode
            if mode == "ap":
                # AP mode: use fixed IP
                from g1_app.utils.arp_discovery import G1_AP_IP
                robot_ip = G1_AP_IP
                logger.info(f"AP mode connection to {robot_ip}")
                
            elif ip:
                # Manual IP provided
                robot_ip = ip
                logger.info(f"Manual IP connection to {robot_ip}")
                
            else:
                # Auto-discover IP from MAC
                logger.info(f"Auto-discovering robot IP for MAC {mac}...")
                from g1_app.utils.robot_discovery import discover_robot
                discovered = discover_robot(target_mac=mac, verify_with_ping=True)
                
                if not discovered:
                    return {
                        "success": False,
                        "error": "Robot not found on network",
                        "suggestions": [
                            "Check if robot is powered on",
                            "Ensure robot is on same WiFi network",
                            "Try AP mode: Connect to robot's WiFi 'G1_xxxx'"
                        ]
                    }
                
                robot_ip = discovered['ip']
                logger.info(f"Discovered robot at {robot_ip}")
            
            # Verify robot is reachable
            from g1_app.utils.arp_discovery import ping_test
            if not ping_test(robot_ip, timeout=2):
                return {
                    "success": False,
                    "error": f"Robot at {robot_ip} is not reachable",
                    "suggestions": [
                        "Verify robot is powered on",
                        "Check network connection",
                        "Try AP mode if on different network"
                    ]
                }
            
            # Connect
            try:
                robot = RobotController(robot_ip, serial_number)
                await robot.connect()
            except Exception as e:
                logger.error(f"Failed to connect to robot: {e}")
                robot = None
                return {
                    "success": False,
                    "error": f"Connection failed: {str(e)}",
                    "suggestions": ["Check robot is in correct mode", "Try restarting robot"]
                }
        
        # Get initial state
        state = robot.current_state
        allowed = robot.state_machine.get_allowed_transitions()
        
        # Pause discovery while connected
        discovery = get_discovery()
        await discovery.stop(clear=False)

        return {
            "success": True,
            "robot": {
                "mac": mac,
                "serial_number": serial_number,
                "ip": robot_ip,
                "mode": mode
            },
            "state": {
                "fsm_state": state.fsm_state.name,
                "fsm_state_value": state.fsm_state.value,
                "led_color": state.led_color.value,
                "allowed_transitions": [s.name for s in allowed]
            }
        }
        
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return {
            "success": False,
            "error": str(e),
            "suggestions": ["Check robot power", "Verify network", "Try different mode"]
        }
```

## 5. Settings Page for Robot Management

**Create new file: `g1_app/ui/templates/settings.html` or add to existing `index.html`:**

```html
<!-- Settings Modal (separate from connection) -->
<div id="settingsModal" class="modal">
    <div class="modal-content" style="max-width: 600px;">
        <div class="modal-title">⚙️ Robot Management</div>
        
        <!-- Robot List -->
        <div class="section">
            <h3>Saved Robots</h3>
            <div id="robotList" class="robot-list">
                <!-- Populated dynamically -->
            </div>
        </div>
        
        <!-- Add New Robot -->
        <div class="section">
            <h3>Add New Robot</h3>
            <div class="form-group">
                <label class="form-label">Nickname</label>
                <input type="text" id="newRobotNickname" class="form-input" placeholder="e.g., Kitchen G1">
            </div>
            <div class="form-group">
                <label class="form-label">
                    MAC Address
                    <span class="help-icon" title="Format: fc:23:cd:92:60:02">?</span>
                </label>
                <input type="text" id="newRobotMac" class="form-input" placeholder="fc:23:cd:92:60:02">
            </div>
            <div class="form-group">
                <label class="form-label">
                    Serial Number
                    <span class="help-icon" title="Found on robot label">?</span>
                </label>
                <input type="text" id="newRobotSerial" class="form-input" placeholder="E21D1000PAHBMB06">
            </div>
            <button class="btn-primary" onclick="addRobotFromSettings()">Add Robot</button>
        </div>
        
        <div class="form-buttons">
            <button class="btn-secondary" onclick="closeSettingsModal()">Close</button>
        </div>
    </div>
</div>

<!-- Add gear icon to top bar -->
<div class="top-bar">
    <!-- existing content -->
    <button class="icon-btn" onclick="openSettingsModal()" title="Settings">
        ⚙️
    </button>
</div>

<style>
.robot-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.robot-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
}

.robot-item-info {
    flex: 1;
}

.robot-item-name {
    font-weight: 600;
    color: var(--primary);
}

.robot-item-details {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
}

.icon-btn {
    background: transparent;
    border: none;
    font-size: 20px;
    cursor: pointer;
    padding: 8px;
    border-radius: 4px;
    transition: background 0.2s;
}

.icon-btn:hover {
    background: rgba(255, 255, 255, 0.1);
}

.section {
    margin: 20px 0;
    padding: 15px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.section:last-child {
    border-bottom: none;
}

.section h3 {
    margin-bottom: 15px;
    color: var(--text-light);
}
</style>
```

---

## Testing Checklist

- [ ] AP mode detection works (ping 192.168.12.1)
- [ ] WiFi SSID detection works on Linux/Windows
- [ ] Discovery progress shows correctly
- [ ] Error messages are helpful
- [ ] Button states update correctly (loading, connected)
- [ ] Settings modal separate from connection
- [ ] IP field hidden from main flow
- [ ] Troubleshooting tips appear on failure

---

## Migration Path

1. **Phase 1**: Add network mode selector (keep old fields for now)
2. **Phase 2**: Add discovery progress indicator
3. **Phase 3**: Hide IP field (move to advanced)
4. **Phase 4**: Move "Add Robot" to settings
5. **Phase 5**: Remove old connection flow entirely

This allows incremental rollout and easy rollback if issues arise.
