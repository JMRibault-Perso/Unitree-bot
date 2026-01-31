#!/usr/bin/env python3
"""
Teach Mode PCAP Analysis
Analyzes PCAPdroid capture using Python SDK teach mode APIs as baseline
Searches for:
- API 7107: GetActionList (get custom actions)
- API 7108: ExecuteCustomAction (play custom action)
- API 7113: StopCustomAction (stop action)
"""

import json
import struct
from pathlib import Path
from collections import defaultdict

# Try to import scapy for PCAP parsing
try:
    from scapy.all import rdpcap, IP, UDP, TCP, Raw
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("⚠️  Scapy not installed. Install with: pip install scapy")

class TeachModeAnalyzer:
    """Analyze PCAP for teach mode protocol"""
    
    # Known teach mode API IDs from Python SDK
    API_IDS = {
        7107: "GetActionList",
        7108: "ExecuteCustomAction", 
        7109: "RecordCustomAction",
        7110: "DeleteCustomAction",
        7111: "GetCustomActionList",
        7112: "ClearCustomActions",
        7113: "StopCustomAction",
    }
    
    # Service names
    SERVICES = {
        "sport": "Locomotion/FSM",
        "arm": "Arm/Gesture",
        "vui": "Audio/LED",
    }
    
    def __init__(self, pcap_file):
        self.pcap_file = Path(pcap_file)
        self.packets = []
        self.flows = defaultdict(list)
        self.api_calls = []
        self.json_payloads = []
        
    def analyze(self):
        """Run full analysis"""
        print(f"=" * 70)
        print(f"Teach Mode PCAP Analysis")
        print(f"File: {self.pcap_file.name}")
        print(f"=" * 70)
        
        if not SCAPY_AVAILABLE:
            print("\n⚠️  Scapy required for full PCAP parsing")
            print("Install: pip install scapy")
            return False
        
        if not self.pcap_file.exists():
            print(f"❌ PCAP file not found: {self.pcap_file}")
            return False
        
        print(f"\n📖 Loading PCAP file ({self.pcap_file.stat().st_size / 1024 / 1024:.1f} MB)...")
        
        try:
            packets = rdpcap(str(self.pcap_file))
            print(f"✅ Loaded {len(packets)} packets")
        except Exception as e:
            print(f"❌ Error loading PCAP: {e}")
            return False
        
        self.analyze_packets(packets)
        self.print_results()
        return True
    
    def analyze_packets(self, packets):
        """Analyze each packet in the capture"""
        for packet in packets:
            # Skip non-IP packets
            if not packet.haslayer(IP):
                continue
            
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            protocol = "TCP" if packet.haslayer(TCP) else "UDP" if packet.haslayer(UDP) else "Other"
            
            # Store packet info
            pkt_info = {
                "src": src_ip,
                "dst": dst_ip,
                "protocol": protocol,
                "payload": None,
            }
            
            # Extract payload
            if packet.haslayer(Raw):
                payload = bytes(packet[Raw].load)
                pkt_info["payload"] = payload
                
                # Try to find JSON
                try:
                    json_str = payload.decode('utf-8', errors='ignore')
                    if '{' in json_str and ':' in json_str:
                        # Extract JSON objects
                        start = json_str.find('{')
                        end = json_str.rfind('}') + 1
                        if start >= 0 and end > start:
                            json_obj = json.loads(json_str[start:end])
                            pkt_info["json"] = json_obj
                            self.json_payloads.append({
                                "src": src_ip,
                                "dst": dst_ip,
                                "data": json_obj
                            })
                except:
                    pass
                
                # Search for teach mode markers
                self.search_teach_mode_markers(payload, pkt_info)
            
            self.packets.append(pkt_info)
            
            # Track flows
            flow_key = (src_ip, dst_ip, protocol)
            self.flows[flow_key].append(pkt_info)
    
    def search_teach_mode_markers(self, payload, pkt_info):
        """Search for teach mode API markers in payload"""
        payload_hex = payload.hex()
        payload_str = payload.decode('utf-8', errors='ignore').lower()
        
        # Search for API IDs
        for api_id, api_name in self.API_IDS.items():
            # Search for API ID as string
            if str(api_id) in payload_str:
                pkt_info["api_id"] = api_id
                pkt_info["api_name"] = api_name
                self.api_calls.append({
                    "api_id": api_id,
                    "api_name": api_name,
                    "src": pkt_info["src"],
                    "dst": pkt_info["dst"],
                    "protocol": pkt_info["protocol"],
                })
            
            # Search for API ID as little-endian 4-byte value
            api_hex = struct.pack('<I', api_id).hex()
            if api_hex in payload_hex:
                if "api_id" not in pkt_info:
                    pkt_info["api_id"] = api_id
                    pkt_info["api_name"] = api_name
        
        # Search for keywords
        keywords = {
            "action": "Action/Gesture",
            "teach": "Teach Mode",
            "record": "Recording",
            "custom": "Custom Action",
            "gesture": "Gesture",
        }
        
        for keyword, desc in keywords.items():
            if keyword in payload_str:
                if "keywords" not in pkt_info:
                    pkt_info["keywords"] = []
                pkt_info["keywords"].append(desc)
    
    def print_results(self):
        """Print analysis results"""
        
        # Summary
        print(f"\n📊 Summary")
        print(f"  Total packets: {len(self.packets)}")
        print(f"  Unique flows: {len(self.flows)}")
        print(f"  JSON payloads found: {len(self.json_payloads)}")
        print(f"  API calls detected: {len(self.api_calls)}")
        
        # API Calls
        if self.api_calls:
            print(f"\n🔍 API Calls Detected")
            api_counts = defaultdict(int)
            for call in self.api_calls:
                api_counts[call["api_name"]] += 1
                print(f"  - {call['api_name']} (ID: {call['api_id']})")
                print(f"    {call['src']} → {call['dst']} ({call['protocol']})")
            
            print(f"\n📈 API Call Summary")
            for api_name, count in sorted(api_counts.items()):
                print(f"  {api_name}: {count}x")
        else:
            print(f"\n⚠️  No teach mode API IDs found in payload")
        
        # JSON Payloads
        if self.json_payloads:
            print(f"\n📋 JSON Payloads")
            for i, payload in enumerate(self.json_payloads[:10], 1):
                print(f"\n  [{i}] {payload['src']} → {payload['dst']}")
                print(f"      {json.dumps(payload['data'], indent=6)[:200]}...")
            if len(self.json_payloads) > 10:
                print(f"  ... and {len(self.json_payloads) - 10} more")
        
        # Flows
        print(f"\n🌐 Network Flows")
        for (src, dst, proto), packets in sorted(self.flows.items())[:10]:
            print(f"  {src} → {dst} ({proto}): {len(packets)} packets")
        
        # Recommendations
        self.print_recommendations()
    
    def print_recommendations(self):
        """Print actionable recommendations"""
        print(f"\n💡 Recommendations")
        
        if not self.api_calls:
            print(f"\n  ⚠️  No teach mode APIs detected in capture")
            print(f"  \n  This could mean:")
            print(f"    1. Teach mode traffic uses different protocol (WebRTC, custom)")
            print(f"    2. Actions list is retrieved via HTTP/WebSocket")
            print(f"    3. Commands are encrypted or obfuscated")
            print(f"\n  Next steps:")
            print(f"    1. Check web_server.py for HTTP endpoints")
            print(f"    2. Analyze WebRTC signaling messages")
            print(f"    3. Search decompiled app for 'api/teach' or 'api/action' paths")
            print(f"    4. Look for WebSocket connections in Wireshark")
        else:
            print(f"\n  ✅ Teach mode traffic detected!")
            api_ids = ', '.join(str(c['api_id']) for c in self.api_calls)
            print(f"  API IDs found: {api_ids}")
            print(f"\n  Next steps:")
            print(f"    1. Extract full payload for each API call")
            print(f"    2. Decode parameter format")
            print(f"    3. Map response format for action list")
        
        print(f"\n  Key APIs to implement:")
        print(f"    • 7107: GetActionList → Get all custom actions")
        print(f"    • 7108: ExecuteCustomAction → Play custom action")
        print(f"    • 7113: StopCustomAction → Stop current action")

def search_decompiled_app(app_path, keywords):
    """Search decompiled app for teach mode implementation"""
    print(f"\n📱 Searching Decompiled Android App")
    print(f"  Path: {app_path}")
    
    app_path = Path(app_path)
    if not app_path.exists():
        print(f"  ❌ App path not found")
        return
    
    keywords_found = defaultdict(list)
    search_dirs = [
        app_path / "Unitree_Explore" / "smali",
        app_path / "Unitree_Explore" / "smali_classes2",
        app_path / "Unitree_Explore" / "smali_classes3",
    ]
    
    print(f"\n  Searching for keywords: {', '.join(keywords)}")
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for java_file in search_dir.rglob("*.smali"):
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore').lower()
                for keyword in keywords:
                    if keyword.lower() in content:
                        keywords_found[keyword].append(str(java_file.relative_to(app_path)))
            except:
                pass
    
    if keywords_found:
        print(f"\n  🔍 Found references:")
        for keyword, files in sorted(keywords_found.items()):
            print(f"\n    '{keyword}': {len(files)} files")
            for f in files[:3]:
                print(f"      - {f}")
            if len(files) > 3:
                print(f"      ... and {len(files) - 3} more")
    else:
        print(f"\n  ⚠️  No matches found for: {', '.join(keywords)}")

if __name__ == "__main__":
    import sys
    
    pcap_file = Path("C:/Unitree/G1/Unitree-bot/android_app_decompiled/Unitree_Explore1/PCAPdroid_26_Jan_10_28_24.pcap")
    app_path = Path("C:/Unitree/G1/Unitree-bot/android_app_decompiled")
    
    print("\n🎓 TEACH MODE PROTOCOL ANALYSIS")
    print("=" * 70)
    
    # Analyze PCAP
    analyzer = TeachModeAnalyzer(pcap_file)
    analyzer.analyze()
    
    # Search decompiled app
    print("\n" + "=" * 70)
    keywords = ["action", "teach", "record", "custom", "7107", "7108", "7113", "api/teach", "api/action"]
    search_decompiled_app(app_path, keywords)
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
