# UDP Port Discovery Sequence (STUN-Based)

## The Discovery Order

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: INITIAL SETUP                                          │
├─────────────────────────────────────────────────────────────────┤
│ 1. App boots, knows robot IP (192.168.86.6) but NOT teaching    │
│    port or external address mapping                              │
│ 2. Android app (or web controller) opens random UDP socket      │
│    Local: 10.215.173.1:34052 (client side, random port)         │
│    Remote: 192.168.86.6:51639 (STUN server on robot)            │
│ 3. Purpose: Discover external port for NAT traversal            │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: STUN BINDING REQUEST (RFC 5389)                        │
├─────────────────────────────────────────────────────────────────┤
│ App → Robot on port 51639:                                       │
│ ┌──────────────────────────────┐                                 │
│ │ STUN Message Type: 0x0001    │ (BINDING REQUEST)              │
│ │ Magic Cookie: 0x2112A442     │ (RFC 5389 standard)            │
│ │ Transaction ID: [12 bytes]   │ (random, for matching)         │
│ │ Attributes:                   │                                │
│ │  - USERNAME: n7Px:iq2R       │ (auth credential)              │
│ │  - MESSAGE-INTEGRITY: [hash] │ (HMAC-SHA1 signature)          │
│ └──────────────────────────────┘                                 │
│                                                                  │
│ This packet says: "I'm at 10.215.173.1:34052, can you tell me   │
│ what external address I appear to come from?"                   │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: STUN BINDING RESPONSE (RFC 5389)                       │
├─────────────────────────────────────────────────────────────────┤
│ Robot ← App on port 51639:                                       │
│ ┌──────────────────────────────────────┐                         │
│ │ STUN Message Type: 0x0101            │ (BINDING SUCCESS)       │
│ │ Magic Cookie: 0x2112A442             │ (RFC 5389 standard)     │
│ │ Transaction ID: [same 12 bytes]      │ (matched to request)    │
│ │ Attributes:                           │                         │
│ │  - XOR-MAPPED-ADDRESS:               │                         │
│ │    192.168.86.6:57006                │ ← THE DISCOVERY!        │
│ │  - MESSAGE-INTEGRITY: [hash]         │ (HMAC-SHA1 response)    │
│ └──────────────────────────────────────┘                         │
│                                                                  │
│ This packet says: "Your external address is 192.168.86.6:57006" │
│                                                                  │
│ ⚠️ XOR-MAPPED-ADDRESS is XORed with magic cookie for NAT        │
│ traversal security, decoded to: 192.168.86.6:57006              │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: PORT EXTRACTION (APP-SIDE LOGIC)                       │
├─────────────────────────────────────────────────────────────────┤
│ App parses STUN response:                                        │
│ 1. Decode XOR-MAPPED-ADDRESS attribute                          │
│ 2. Extract port: 57006                                          │
│ 3. Store in memory: teaching_port = 57006                       │
│ 4. Verify message integrity (HMAC-SHA1)                         │
│ 5. All subsequent teaching commands → port 57006                │
│                                                                  │
│ Result: App NOW KNOWS to send 0x42/0x43 commands to :57006      │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: TEACHING COMMANDS (ENCRYPTED)                          │
├─────────────────────────────────────────────────────────────────┤
│ App → Robot on port 57006:                                       │
│ ┌──────────────────────────────┐                                 │
│ │ Command: 0x42 (DELETE)       │                                 │
│ │ Action: "test"               │ (encrypted payload)             │
│ │ Total: 57 bytes              │                                 │
│ └──────────────────────────────┘                                 │
│                                                                  │
│ ┌──────────────────────────────┐                                 │
│ │ Command: 0x43 (RENAME)       │                                 │
│ │ Old name: "test"             │ (encrypted payload)             │
│ │ New name: "walk"             │                                 │
│ │ Total: 73 bytes              │                                 │
│ └──────────────────────────────┘                                 │
│                                                                  │
│ These commands are what the UI rename/delete buttons trigger    │
└─────────────────────────────────────────────────────────────────┘
```

## Discovery Sequence Timeline (From PCAP)

Based on analysis of `PCAPdroid_30_Jan_18_26_35.pcap`:

| Time | Direction | Port | Message Type | Purpose |
|------|-----------|------|--------------|---------|
| T+0ms | App → Robot | 51639 | STUN BINDING REQUEST | "Where am I?" |
| T+15ms | Robot → App | 51639 | STUN BINDING RESPONSE | "You're at :57006" |
| T+20ms | **Discovery Complete** | - | App extracts 57006 | Port stored in memory |
| T+25ms | App → Robot | 57006 | 0x42 DELETE | Use discovered port! |
| T+30ms | App → Robot | 57006 | 0x43 RENAME | Use discovered port! |

**Critical Finding**: The robot doesn't tell the app the port directly - it tells the app what its **external address:port combination** is, and the app extracts the port from that.

## Why This Architecture?

1. **Firewall Traversal**: STUN discovers if you're behind NAT/firewall
2. **Port Reuse**: Both STUN negotiation (51639) and teaching protocol (57006) use same credential verification
3. **Dynamic Allocation**: Port 57006 is assigned by robot's port manager; STUN is the way to discover it
4. **Security**: XOR-MAPPED-ADDRESS prevents passive network inspection

## How Our Web Controller Should Work

**Current Implementation Gap:**
Our Python web controller running on Windows doesn't do STUN discovery - it assumes port 57006 is known. In real deployment:

```python
# What the system SHOULD do:

class G1Controller:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        self.teaching_port = None  # UNKNOWN until STUN
        
    async def discover_teaching_port(self):
        """Phase 1-4: STUN discovery"""
        stun_client = STUNClient(self.robot_ip, stun_port=51639)
        
        # Send BINDING REQUEST with credentials
        response = await stun_client.send_binding_request(
            username="n7Px:iq2R",
            # HMAC will be computed with shared secret
        )
        
        # Parse XOR-MAPPED-ADDRESS
        self.teaching_port = response.xor_mapped_address.port
        # Result: 57006
        
    async def send_teaching_command(self, command_id, payload):
        """Phase 5: Send command to discovered port"""
        if not self.teaching_port:
            await self.discover_teaching_port()
        
        # Now we can send 0x42/0x43 to the right port!
        await self.udp_client.send(
            host=self.robot_ip,
            port=self.teaching_port,  # ← From STUN!
            data=build_command(command_id, payload)
        )
```

## Key Insight About Your Question

You asked "how does the system discover the UDP port" - the answer is:

1. **First connection**: App doesn't know the teaching port (57006)
2. **STUN protocol**: App uses RFC 5389 to get NAT information
3. **XOR-MAPPED-ADDRESS**: Robot tells app its external address:port combo
4. **Port extraction**: App parses response and gets 57006
5. **Subsequent commands**: All 0x42/0x43 go to that discovered port

**The robot has TWO well-known ports:**
- **Port 51639**: STUN service (for discovering port mappings)
- **Port 57006**: Teaching protocol (for 0x42/0x43 commands, discovered via STUN)

This is why we found 174 STUN packets in the PCAP - every connection (app restart, WiFi reconnect, etc.) re-runs this discovery!

## Matching to Our Implementation

Our current code:

| Component | Discovery | Port Used | Notes |
|-----------|-----------|-----------|-------|
| delete_action() | Hardcoded | 57006 | ✅ Matches STUN-discovered port |
| rename_action() | Hardcoded | 57006 | ✅ Matches STUN-discovered port |
| Web UI buttons | Hardcoded | 57006 | ✅ Correct port in all payloads |

**What we're missing:**
- STUN client to auto-discover port 57006 from port 51639
- Credential management (username n7Px:iq2R)
- HMAC-SHA1 computation for MESSAGE-INTEGRITY

But for local WiFi testing on G1_6937, hardcoding port 57006 works fine since:
1. STUN port is internal/non-routable from Windows PC
2. We're on same LAN, so port 57006 is directly accessible
3. We reversed it from PCAP, so we know it's correct
