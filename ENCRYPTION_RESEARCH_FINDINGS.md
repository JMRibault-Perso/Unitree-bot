# 🔐 Unitree G1 Encryption Discovery - Security Research Findings

## ✅ Key Findings from Security Research

### Sources
1. **Medium Article**: "The Unitree G1 Security Crisis" by CreedTec (Oct 2025)
   - Focus: BLE/Configuration security, data exfiltration
   
2. **arXiv Paper**: 2509.14139
   - Academic technical analysis of G1 vulnerabilities

---

## 🔑 KNOWN ENCRYPTION KEYS (Confirmed by Research)

### 1. UniPwn BLE Encryption
- **Type**: AES (hardcoded)
- **Key Property**: **Identical across ALL Unitree robots** (G1, H1, Go2, B2, R1)
- **Purpose**: Protects Wi-Fi provisioning via Bluetooth
- **Attack**: Encrypt "unitree" with key → gain root access
- **Status**: ⚠️ Known in security community

### 2. FMX Configuration Encryption
- **Type**: Blowfish-ECB (static)
- **Key Property**: **Fleet-wide key** - same across all robots
- **Purpose**: Protects configuration files
- **Status**: ⚠️ Broken encryption per research

### 3. Teaching Protocol (0x43 Rename)
- **Type**: Unknown ❓ (Tested: NOT simple AES or Blowfish)
- **Status**: Still encrypted
- **Hypothesis**: 
  - Custom cipher
  - Different key derivation
  - Binary encoding (not traditional encryption)

---

## 🎯 Why Known Keys Didn't Work on PCAP

The teaching protocol (0x43 rename) appears to use **different encryption** than:
- ✗ UniPwn's hardcoded AES key
- ✗ FMX's Blowfish key
- ✗ Simple XOR encryption

### Possible Explanations:
1. **Custom cipher** designed specifically for teaching mode
2. **Per-robot key** derived from serial number/MAC
3. **Session-based key** generated during connection
4. **Binary protocol** (not cryptographic, just binary encoding)

---

## 📊 Attack Surface from Research

| Component | Encryption | Key | Exploitable |
|-----------|------------|-----|------------|
| BLE Provisioning | AES | Hardcoded "unitree" | ✅ YES (UniPwn) |
| Configuration (FMX) | Blowfish-ECB | Fleet-wide static | ✅ YES (Known key) |
| Teaching Protocol | ??? | Unknown | ❓ TBD |
| MQTT to China | Unencrypted | N/A | ✅ YES (passive wiretap) |
| DDS Internal | Unencrypted | N/A | ✅ YES (network sniff) |

---

## 🔍 Research-Backed Decryption Approaches

### Approach 1: Find Teaching Protocol Key (Recommended)
Since UniPwn/FMX keys don't work, the teaching protocol likely has a **different key**. Try:

```bash
# Extract all key-like constants from app
strings android_app_decompiled/lib/arm64-v8a/*.so | grep -E '^[a-f0-9]{32,}$'

# Look for "rename" or "0x43" handlers
grep -r "0x43\|rename\|teach" android_app_decompiled/smali/

# Find key derivation
grep -r "MD5\|SHA1\|SHA256\|HMAC\|derive\|kdf" android_app_decompiled/
```

### Approach 2: Analyze MQTT Traffic (Unencrypted!)
Good news: The research shows robot **sends data via unencrypted MQTT to China**

```bash
# The MQTT traffic is NOT encrypted
# This means we can see what data structures look like
# Maybe teaching action names appear in MQTT messages!

tcpdump -i eth0 'tcp port 1883 or udp port 1883' -w mqtt_capture.pcap
# MQTT is human-readable protocol - action names might be visible
```

### Approach 3: Reverse UniPwn Exploit
The UniPwn research is public. Use it to:
1. Exploit BLE provisioning (get root)
2. Access robot's filesystem directly
3. Extract hardcoded teaching keys from binary

### Approach 4: Check arXiv for Technical Details
The paper may contain:
- Exact encryption algorithm used
- Key derivation method
- Protocol specification

---

## 🎁 BONUS: What We CAN Access (Unencrypted)

The research confirms these are **unencrypted or weakly protected**:

1. **DDS Topics** (internal robot comms)
   - rt/lowstate (all sensor data)
   - rt/lowcmd (all motor commands)
   - rt/audio_msg (microphone feed!)
   - rt/utlidar/cloud (LIDAR point cloud!)

2. **MQTT Topics** (to Chinese servers)
   - Every 5 minutes telemetry dump
   - Battery, motors, system state
   - Video/audio streams referenced

3. **BLE Provisioning** (if unprotected)
   - Wi-Fi credentials
   - Network configuration

---

## 💡 Recommended Next Action

**Most Likely to Succeed:**

1. **Check if action names appear in MQTT** 
   - Capture unencrypted MQTT traffic
   - Look for "test" or other action names
   - No crypto needed!

2. **Use UniPwn to root robot**
   - Get filesystem access
   - Extract teaching protocol key from binary
   - Decrypt PCAP with extracted key

3. **Extract from decompiled app**
   - Search for string "test" in smali code
   - Find encryption function that uses it
   - Trace back to key source

---

## 📎 Security Research References

- **UniPwn GitHub**: https://github.com/Bin4ry/UniPwn
- **CVE Identifier**: Assigned (check NVD for "Unitree")
- **Responsible Disclosure**: Unitree contacted but reportedly not engaging
- **IEEE Spectrum Coverage**: Security analysis published
- **arXiv**: 2509.14139 (full technical paper)

---

## ⚠️ Important Note

The teaching protocol encryption you're investigating might be:
- **Intentionally weak** (for embedded performance)
- **Different per-robot** (derived from serial/MAC)
- **Session-based** (changes per connection)
- **Not encryption** (just binary packing)

Given that Unitree is already exposed for:
- Hardcoded BLE keys
- Fleet-wide FMX keys
- Unencrypted MQTT
- Unencrypted DDS

...it's likely the teaching protocol uses a **publicly derivable key or weak encryption**.

---

## 🚀 Testing Priority

1. **HIGH**: Extract packet traces from decompiled app (fastest)
2. **HIGH**: Capture MQTT traffic (already unencrypted)
3. **MEDIUM**: Use UniPwn to root device for key extraction
4. **MEDIUM**: Search app binary for encryption keys with strings/grep
5. **LOW**: Brute force (2^256 possibilities)

---

## Next Steps for WSL

Push research findings to git so WSL team can:
1. Download android_app_decompiled
2. Search for teaching protocol keys
3. Analyze MQTT unencrypted traffic  
4. Test UniPwn exploitation if robot available
