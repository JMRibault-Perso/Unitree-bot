# Teaching Protocol Commands - Decrypted from PCAPdroid_30_Jan_23_50_46.pcap

## Capture Details
- **Date**: January 30, 2026 at 23:50:50
- **TLS Decryption**: Enabled (successfully exposed WebRTC datachannel)
- **Actions Performed**:
  1. PLAY "handshake" action
  2. DELETE "AAAAAAAAA" action

---

## PLAY_ACTION Command (0x41)

### Packet Details
- **Packet Number**: #122
- **Timestamp**: 23:50:50.254
- **Direction**: PHONE → ROBOT (192.168.86.3:56017 → 10.215.173.1:53338)
- **Total Length**: 189 bytes
- **Action Played**: "handshake"

### Complete Hex Payload
```
17fefd000100000000000f00b041cb5fbc04be132724daaba88e9e68622c1577ef
db3e5542108ac4edc1f427d2167478e4af56f101b2615d4be36c52436e738d49
7ab39a4333591358c0f709368b330afb8b5a25337880e5298b8233c12161e82d
ee367a5ab6ca7e92cec940a6a5ba3c43c8d50ec96ecba4478130d9a2ca9402dc
4840777f30e7958473f594af56f415949b24778f631ab2093ad00b716039dfe6
2c794b7cf0e5415ba2281f930a688b822fb08d778200e9aea27dddaf
```

### Structure Analysis
```
Offset | Length | Field           | Value (hex)
-------|--------|-----------------|------------------
0-2    | 3      | Magic Header    | 17 FE FD
3-12   | 10     | Sequence/Flags  | 00 01 00 00 00 00 00 0F 00 B0
13     | 1      | Command         | 41 (PLAY_ACTION)
14-15  | 2      | Payload Length  | CB 5F (52063 - ENCRYPTED)
16+    | vary   | Encrypted Data  | (action name + parameters)
```

**Note**: The payload is still encrypted even after TLS decryption. This indicates the teaching protocol has an **additional encryption layer** on top of WebRTC DTLS.

---

## DELETE_ACTION Command (0x42)

### Packet Details
- **Packet Number**: #390
- **Timestamp**: 23:50:52.708 (+2.454s after PLAY)
- **Direction**: PHONE → ROBOT (192.168.86.3:56017 → 10.215.173.1:53338)
- **Total Length**: 237 bytes
- **Action Deleted**: "AAAAAAAAA" (9 characters)

### Complete Hex Payload
```
17fefd00010000000000a800e0426cecf1edc89709e872bedd5d80befc4b5409
7f999980d09be0772b6e2e1f7390134967568804c822b6d6abbdc527948557d9
5b220297d63e1081ea620e1dd3c9230e8668ecc1803a42a4a5304cca854cd63
89c3bf160ac06fe82682f8f1ec7ce0e9e30f83404aa1a110b82ece73f4998830
50dc986bbed7be59f2ef7d984ebff406959f7d642e7bc955fd535e32f1413b06
83bbc94c6b65431926471712ec9cae1ae225627d89653b9074b127ee2f7f0ff3
f655d990feae8b22afa3577c76082d083e2159fc98e4f4df4f7c763fcd98bf81
014b91137c36d6703e36448daaf
```

### Structure Analysis
```
Offset | Length | Field           | Value (hex)
-------|--------|-----------------|------------------
0-2    | 3      | Magic Header    | 17 FE FD
3-12   | 10     | Sequence/Flags  | 00 01 00 00 00 00 00 A8 00 E0
13     | 1      | Command         | 42 (DELETE_ACTION)
14-15  | 2      | Payload Length  | 6C EC (27884 - ENCRYPTED)
16+    | vary   | Encrypted Data  | (action name to delete)
```

**Note**: The payload length field appears to be encrypted or obfuscated. The actual payload is only ~220 bytes, not 27,884 bytes.

---

## Key Findings

### 1. **Double Encryption Layer**
- **Layer 1**: WebRTC DTLS 1.2 (successfully decrypted with TLS keylog)
- **Layer 2**: Teaching protocol encryption (NOT decrypted)
  - The magic header `17 FE FD` is visible
  - Command byte (0x41, 0x42) is visible
  - But payload (action names, parameters) is still encrypted

### 2. **Packet Size Correlation**
- DELETE "AAAAAAAAA" (9 chars): **237 bytes**
- PLAY "handshake" (9 chars): **189 bytes**
- Similar action name lengths result in different packet sizes
- Suggests encryption includes padding or additional metadata

### 3. **Payload Length Field**
- Appears to be encrypted or contains additional flags
- Does not match actual packet payload size
- May be XORed with a sequence number or key

### 4. **Command Byte is Cleartext**
At offset 13, the command byte is NOT encrypted:
- `0x41` = PLAY_ACTION ✓
- `0x42` = DELETE_ACTION ✓
- `0x43` = RENAME_ACTION (from previous analysis) ✓
- `0x1A` = GET_ACTION_LIST (from previous analysis) ✓

### 5. **Next Steps to Full Decryption**
To decrypt the second layer (action names), we need:

**Option A: Known-Plaintext Attack** (RECOMMENDED)
- Capture DELETE/PLAY for known action names
- Use XOR cipher property to extract keystream
- Example: If we PLAY "handshake", we know bytes 18-26 should be `handshake\x00`
- XOR encrypted bytes with known plaintext to get keystream

**Option B: Reverse-Engineer Encryption Algorithm**
- Decompile Unitree Android app APK
- Find teaching protocol encryption code
- Implement decryption in Python

**Option C: Man-in-the-Middle with Modified App**
- Root Android phone
- Hook into app's memory to capture pre-encryption payloads
- Use Frida or Xposed framework

---

## Comparison with Previous Analysis

In earlier PCAPs (PCAPdroid_30_Jan), we successfully decrypted **RENAME commands (0x43)** using known-plaintext attack:
- Target name: "AAAAAAAAA" (10 'A's)
- Known bytes: `41 41 41 41 41 41 41 41 41 41 00` (10 A's + null terminator)
- Successfully extracted 17 XOR keystreams

**We can apply the same technique here!**

### For PLAY "handshake" (Packet #122):
- Known plaintext at offset ~18: `handshake\x00` = `68 61 6E 64 73 68 61 6B 65 00`
- Encrypted bytes: `cb 5f bc 04 be 13 27 24 da ab a8 8e 9e 68...`
- XOR to get keystream (if simple XOR): 
  ```
  Keystream[0] = 0xCB XOR 0x68 = 0xA3
  Keystream[1] = 0x5F XOR 0x61 = 0x3E
  ... and so on
  ```

### For DELETE "AAAAAAAAA" (Packet #390):
- Known plaintext at offset ~18: `AAAAAAAAA\x00` = `41 41 41 41 41 41 41 41 41 41 00`
- Encrypted bytes: `6c ec f1 ed c8 97 09 e8 72 be dd 5d...`
- XOR to extract keystream

---

## Implementation Plan

1. **Create known-plaintext XOR decoder**
   - Extract encrypted bytes starting at offset 16-18 (after payload length)
   - XOR with known action names
   - Verify if decryption reveals cleartext

2. **Test with multiple actions**
   - Play/delete different actions with known names
   - Compare XOR keys to find pattern

3. **Document encryption algorithm**
   - If XOR: find key generation method
   - If stream cipher: identify algorithm (RC4, ChaCha20, etc.)

4. **Build full protocol implementation**
   - Implement encryption/decryption
   - Create Python client that can send encrypted commands
   - Replicate Android app functionality

---

## Quick Test Command

To verify if it's simple XOR with "handshake" at offset 16:
```python
encrypted = bytes.fromhex("cb5fbc04be132724daaba88e9e68")
known = b"handshake\x00"
keystream = bytes([e ^ k for e, k in zip(encrypted, known)])
print(keystream.hex())
```

Expected: If simple XOR, the keystream should be consistent or follow a pattern.
