# PCAP Decryption Methods - Analysis

## 🔐 Current Status: Binary Payload Encryption Suspected

### Evidence of Encryption
- Rename (0x43) packet payloads display as **binary/corrupted text**
- Example: `'═s)=u=1;░ـtEz\░[░1-zF░r░/!' → 'g░░i~░░░░░░░░░9Kz░⚹░░░░B4░s░'`
- Pattern suggests: **XOR, AES, or custom cipher**
- **"test" literal NOT found** in plaintext search, yet rename packets exist (103 packets)

---

## 🔧 Decryption Approaches (Ranked by Feasibility)

### Approach 1: XOR with Simple Key (Most Likely - G1 IoT Device)
**Probability: HIGH** ✅

G1 often uses simple XOR encryption for speed on embedded systems.

**Detection Method:**
```python
def detect_xor_pattern(payload):
    """Find repeating XOR key pattern"""
    # XOR repeats every N bytes (typical: 4, 8, 16, 32)
    for key_len in [4, 8, 16, 32]:
        patterns = set()
        for i in range(0, len(payload) - key_len, key_len):
            chunk = payload[i:i+key_len]
            patterns.add(chunk)
        
        # If few unique patterns, likely XOR
        if len(patterns) < len(payload) / (key_len * 2):
            print(f"Possible XOR key length: {key_len}")
            return patterns.pop()
```

**Known XOR Keys to Try:**
- `0xAA` (single byte)
- `0x12345678` (4 bytes - common)
- Robot serial number bytes
- Hardcoded in app code

**Tools:**
```bash
# Using Scapy + custom script
python3 xor_decrypt.py PCAPdroid_30_Jan_18_26_35.pcap

# Or manual in Python
key = bytes([0xAA, 0xBB, 0xCC, 0xDD])
decrypted = bytes(a ^ b for a, b in zip(encrypted_payload, key * (len(payload)//4)))
```

---

### Approach 2: Reverse-Engineer Android App (Medium Effort)
**Probability: HIGH** ✅

The Android app contains the encryption/decryption logic.

**Files to Examine:**
1. **Located**: `android_app_decompiled/Unitree_Explore/`
2. **Search Terms**:
   - `encrypt`, `decrypt`, `cipher`
   - `rename`, `action`, `0x43`
   - Method names: `encode()`, `decode()`, `process()`, `transform()`

**Steps:**
```bash
# 1. Decompile if not already done
cd android_app_decompiled
java -jar apktool.jar d -f Unitree_Explore.apk -o Unitree_Explore_decompiled

# 2. Search for encryption
grep -r "encrypt\|decrypt\|XOR\|AES" Unitree_Explore_decompiled/

# 3. Look for hardcoded keys
grep -r "0x[0-9A-F]" Unitree_Explore_decompiled/smali/ | head -50

# 4. Check native libraries (.so files) - may contain encryption
find Unitree_Explore_decompiled -name "*.so" -exec strings {} \; | grep -i crypt
```

**If Baidu Protected:**
- Main code likely in `smali_assets/baiduprotect*/com/unitree/`
- May need **Frida hooking** to extract at runtime

---

### Approach 3: Known Plaintext Attack (High Success Rate)
**Probability: VERY HIGH** ✅

If we know what the plaintext should be, we can deduce the key.

**Known Values:**
- Action names you used (e.g., "test")
- Fixed fields (timestamps, IDs)
- Null bytes in padding

**Example:**
```python
# We know old_name field is 32 bytes
# First rename packet: decrypt both directions
known_plaintext = b'test_action_name' + b'\x00' * 16  # 32 bytes
ciphertext = encrypted_payload[0:32]

# Try XOR
for key_byte in range(256):
    test_key = bytes([key_byte] * 32)
    decrypted = bytes(a ^ b for a, b in zip(ciphertext, test_key))
    if b'test' in decrypted:
        print(f"Found key byte: 0x{key_byte:02X}")
```

**Action: Manually Test Known Names**
1. You renamed something to "test" → capture that packet
2. Extract bytes 0-31 from 0x43 payload
3. Brute force single-byte XOR (256 tries)
4. Check if any result contains readable ASCII

---

### Approach 4: Capture Plaintext + Ciphertext Pair (Direct Method)
**Probability: HIGHEST** ✅✅✅

**Best approach: Capture while we control the input**

```bash
# 1. Get fresh PCAP while renaming to known string
tcpdump -i eth0 host 192.168.86.3 -w fresh_capture.pcap

# 2. In Android app: Rename "action_1" → "MyTestName123"
# (Something you typed, so you know exactly what it is)

# 3. Analyze the packet:
python3 -c "
import struct
# Read 0x43 packet payload
payload = bytes.fromhex('...')
old = payload[0:32]
new = payload[32:64]
print(f'Old encrypted: {old.hex()}')
print(f'New encrypted: {new.hex()}')

# Try XOR with known text
known = 'MyTestName123' + chr(0) * 19  # pad to 32
key = bytes(a ^ b for a, b in zip(new, known.encode()))
print(f'Possible key: {key.hex()}')

# Apply to old_name
old_decrypted = bytes(a ^ b for a, b in zip(old, key * 2))
print(f'Old name decrypted: {old_decrypted}')
"
```

---

### Approach 5: Frida Runtime Hooking (Advanced)
**Probability: HIGH** ✅
**Difficulty: Medium**

If the app is protected, hook at runtime to see plaintext.

**frida-server already available**: `android_app_decompiled/frida-server*`

```javascript
// hook-decrypt.js - Hook decryption function
Java.perform(function() {
    var Cipher = Java.use("javax.crypto.Cipher");
    var original_doFinal = Cipher.doFinal.overload("[B");
    
    original_doFinal.implementation = function(input) {
        console.log("[*] Decryption called");
        console.log("[*] Input: " + Java.use("java.util.Arrays").toString(input));
        
        var result = this.doFinal(input);
        console.log("[*] Output: " + Java.use("java.util.Arrays").toString(result));
        return result;
    };
});
```

---

## 🎯 Recommended Approach: Combined Method

### Step 1: Quick XOR Brute Force (5 minutes)
```bash
python3 xor_brute_force.py PCAPdroid_30_Jan_18_26_35.pcap
# Tests: single-byte XOR, common patterns
```

### Step 2: If XOR Fails → Known Plaintext (15 minutes)
```bash
# You know "test" exists in rename packets
# Extract 0x43 payloads, try XOR with "test" + padding
python3 known_plaintext_attack.py --target test
```

### Step 3: If Still No Luck → Decompile App (30 minutes)
```bash
# Search for "rename", "0x43", encryption functions
grep -r "rename\|43\|encrypt" Unitree_Explore_decompiled/
# Look for hardcoded key constants
```

### Step 4: Last Resort → Capture Fresh PCAP (Best)
```bash
# With controlled input, guaranteed success
# Rename to "AAAAAAAAAA..." (30x A's)
# Extract encrypted payload
# Compare pattern to find XOR key
```

---

## 📝 Scripts to Create

### xor_brute_force.py
```python
#!/usr/bin/env python3
"""Try common XOR patterns on PCAP payloads"""

import struct

def test_xor_single_byte(data):
    """Test all 256 single-byte XOR keys"""
    for key_byte in range(256):
        decrypted = bytes(b ^ key_byte for b in data)
        if has_valid_ascii(decrypted):
            return key_byte, decrypted
    return None, None

def has_valid_ascii(data):
    """Check if data contains printable ASCII"""
    printable = sum(1 for b in data if 32 <= b < 127 or b == 0)
    return printable / len(data) > 0.7  # 70% printable

# Try on all 0x43 packets
# Report if any decrypt to readable text
```

### known_plaintext_attack.py
```python
#!/usr/bin/env python3
"""Use known plaintext (e.g., 'test') to find XOR key"""

def find_xor_key_from_known_plaintext(ciphertext, known_plaintext):
    """
    If we know some plaintext, derive the XOR key
    """
    # Pad known plaintext to match ciphertext length
    plaintext = known_plaintext.ljust(len(ciphertext), '\x00')
    
    # XOR = ciphertext ^ plaintext
    key = bytes(a ^ b for a, b in zip(ciphertext, plaintext.encode()))
    
    return key

# Find key from any 0x43 packet where old_name = "test"
# Then apply to all other packets
```

---

## 🔑 Key Indicators to Look For

**If encryption exists:**
- High entropy in payload (close to 1.0 for random data)
- No repeating ASCII patterns
- Payload length always fixed (32-byte fields)

**If NOT encrypted (or weak encryption):**
- Plaintext strings visible in hex dump
- Common patterns (nulls, repeating bytes)
- Human-readable names in capture

---

## ✅ Quick Check: Is This Encrypted?

```bash
# Extract all 0x43 payload data
python3 -c "
import struct

with open('PCAPdroid_30_Jan_18_26_35.pcap', 'rb') as f:
    data = f.read()

# Find 0x43 packets
pos = 0
while True:
    pos = data.find(b'\\x17\\xfe', pos)
    if pos == -1: break
    if pos + 13 < len(data) and data[pos + 13] == 0x43:
        payload = data[pos + 16:pos + 48]  # First 32 bytes
        entropy = calculate_entropy(payload)
        print(f'Entropy: {entropy:.2f} - {payload.hex()[:32]}...')
    pos += 1

def calculate_entropy(data):
    from collections import Counter
    counts = Counter(data)
    return -sum(c/len(data) * __import__('math').log2(c/len(data)) for c in counts.values())
"

# Entropy > 7.0 = highly likely encrypted
# Entropy < 5.0 = likely plaintext or weak encryption
```

---

## 📚 Resources

- **Wireshark Decryption Guide**: https://wiki.wireshark.org/HowToDecrypt802.11
- **XOR Cipher Analysis**: https://en.wikipedia.org/wiki/XOR_cipher#Cryptanalysis
- **APKTool**: Already in `android_app_decompiled/apktool.jar`
- **Frida**: Already in `android_app_decompiled/frida-server*`

---

## 🎯 Next Actions

**Immediate (High Success):**
1. Run XOR brute force on 0x43 packets
2. Look for "test" in decrypted results
3. If found, we have the key for all payloads

**If Not Found:**
1. Capture new PCAP with controlled input
2. Rename to "AAAAAAAAAA..." (repeating pattern)
3. Extract and analyze encrypted version
4. Extract key and decrypt all historical data

**Recommended Order:**
1. ✅ Quick XOR test (5 min)
2. ✅ Known plaintext "test" (5 min)
3. → If working: Decrypt entire PCAP (2 min)
4. → If not: Capture fresh (30 min, guaranteed success)

---

## 💡 Success Indicators

**You'll know encryption is solved when:**
- 0x43 packet old_name field contains readable text
- 0x43 packet new_name field contains readable text
- Can identify what was renamed to what
- Can decrypt action names from all 103 rename packets
