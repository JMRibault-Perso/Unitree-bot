#!/usr/bin/env python3
"""
Simple PCAP Parser - No dependencies required
Analyzes teach mode PCAP capture for API IDs and patterns
"""

import struct
import json
from pathlib import Path
from collections import defaultdict

class SimplePcapParser:
    """Parse PCAP files without scapy dependency"""
    
    # PCAP file format constants
    PCAP_MAGIC = 0xa1b2c3d4
    PCAP_MAGIC_BE = 0xd4c3b2a1
    
    def __init__(self, pcap_file):
        self.pcap_file = Path(pcap_file)
        self.packets = []
        self.api_calls = defaultdict(list)
        self.json_objects = []
        
    def parse(self):
        """Parse PCAP file"""
        if not self.pcap_file.exists():
            print(f"❌ File not found: {self.pcap_file}")
            return False
        
        try:
            with open(self.pcap_file, 'rb') as f:
                # Read global header
                global_header = f.read(24)
                if len(global_header) < 24:
                    print("❌ Invalid PCAP file (too short)")
                    return False
                
                magic = struct.unpack('<I', global_header[0:4])[0]
                if magic == self.PCAP_MAGIC_BE:
                    endian = '>'  # Big-endian
                elif magic == self.PCAP_MAGIC:
                    endian = '<'  # Little-endian
                else:
                    print(f"❌ Invalid PCAP magic: {magic:08x}")
                    return False
                
                print(f"✅ Valid PCAP file (endian: {'big' if endian == '>' else 'little'})")
                
                # Read packets
                packet_count = 0
                while True:
                    pckt_hdr = f.read(16)
                    if len(pckt_hdr) < 16:
                        break
                    
                    ts_sec, ts_usec, incl_len, orig_len = struct.unpack(f'{endian}4I', pckt_hdr)
                    
                    if incl_len > 0x10000:  # Sanity check
                        break
                    
                    payload = f.read(incl_len)
                    if len(payload) < incl_len:
                        break
                    
                    self.extract_data(payload)
                    packet_count += 1
                
                print(f"✅ Parsed {packet_count} packets")
                return True
        except Exception as e:
            print(f"❌ Error parsing PCAP: {e}")
            return False
    
    def extract_data(self, payload):
        """Extract useful data from packet payload"""
        if len(payload) < 20:
            return
        
        # Try to extract strings and JSON
        payload_hex = payload.hex()
        payload_str = payload.decode('utf-8', errors='ignore')
        
        # Search for teach mode API IDs
        teach_apis = {
            7107: "GetActionList",
            7108: "ExecuteCustomAction",
            7109: "RecordCustomAction", 
            7110: "DeleteCustomAction",
            7111: "GetCustomActionList",
            7112: "ClearCustomActions",
            7113: "StopCustomAction",
        }
        
        for api_id, api_name in teach_apis.items():
            # Search as string
            api_str = str(api_id)
            if api_str in payload_str:
                self.api_calls[api_name].append({
                    "format": "string",
                    "payload_sample": payload[:100].hex()
                })
            
            # Search as little-endian 4-byte int
            api_bytes = struct.pack('<I', api_id).hex()
            if api_bytes in payload_hex:
                self.api_calls[api_name].append({
                    "format": "binary_le",
                    "payload_sample": payload[:100].hex()
                })
        
        # Try to extract JSON
        try:
            # Look for JSON patterns
            if '{' in payload_str and '"' in payload_str:
                # Find JSON boundaries
                start = payload_str.find('{')
                end = payload_str.rfind('}') + 1
                if 0 <= start < end <= len(payload_str):
                    json_str = payload_str[start:end]
                    try:
                        obj = json.loads(json_str)
                        self.json_objects.append(obj)
                    except:
                        pass
        except:
            pass
    
    def print_results(self):
        """Print analysis results"""
        print("\n" + "=" * 70)
        print("📊 TEACH MODE API DETECTION")
        print("=" * 70)
        
        if self.api_calls:
            print("\n✅ TEACH MODE API CALLS FOUND!\n")
            for api_name, calls in sorted(self.api_calls.items()):
                print(f"  🔍 {api_name}: {len(calls)} occurrence(s)")
                for call in calls[:2]:
                    print(f"     Format: {call['format']}")
                    print(f"     Sample: {call['payload_sample'][:50]}...")
        else:
            print("\n⚠️  NO TEACH MODE API IDs DETECTED IN PCAP")
            print("\nThis suggests:")
            print("  • Teach mode uses HTTP/WebSocket protocol (not raw API IDs)")
            print("  • Commands sent as JSON in HTTP POST/WebSocket messages")
            print("  • May need to analyze as HTTP traffic, not UDP packets")
        
        if self.json_objects:
            print(f"\n📋 JSON OBJECTS FOUND: {len(self.json_objects)}")
            for i, obj in enumerate(self.json_objects[:5], 1):
                print(f"\n  [{i}]")
                try:
                    print(f"      {json.dumps(obj, indent=10)[:150]}...")
                except:
                    print(f"      (Could not format)")

class AppSearcher:
    """Search decompiled app for teach mode implementation"""
    
    def __init__(self, app_path):
        self.app_path = Path(app_path)
        self.findings = defaultdict(list)
    
    def search(self, keywords):
        """Search for keywords in app"""
        print(f"\n" + "=" * 70)
        print("📱 DECOMPILED APP ANALYSIS")
        print("=" * 70)
        
        if not self.app_path.exists():
            print(f"❌ App path not found: {self.app_path}")
            return
        
        # Focus on Unitree-specific code
        unitree_dirs = [
            self.app_path / "Unitree_Explore" / "smali" / "com",
            self.app_path / "Unitree_Explore" / "smali_classes2" / "com",
            self.app_path / "Unitree_Explore" / "smali_classes3" / "com",
        ]
        
        print(f"\n🔍 Searching Unitree app code for teach mode...")
        
        for base_dir in unitree_dirs:
            if not base_dir.exists():
                continue
            
            for smali_file in base_dir.rglob("*.smali"):
                try:
                    content = smali_file.read_text(encoding='utf-8', errors='ignore').lower()
                    class_path = str(smali_file.relative_to(self.app_path / "Unitree_Explore"))
                    
                    # Check for teach/action/custom keywords
                    for keyword in keywords:
                        if keyword.lower() in content:
                            self.findings[keyword].append(class_path)
                except:
                    pass
        
        # Print findings
        if self.findings:
            print(f"\n✅ FOUND RELEVANT CODE SECTIONS:\n")
            for keyword, files in sorted(self.findings.items(), key=lambda x: -len(x[1])):
                if len(files) > 0:
                    print(f"  '{keyword}': {len(files)} file(s)")
                    for f in sorted(set(files))[:3]:
                        print(f"    📄 {f}")
                    if len(set(files)) > 3:
                        print(f"    ... and {len(set(files)) - 3} more")
        else:
            print(f"\n⚠️  No teach mode code found in app")
    
    def extract_http_endpoints(self):
        """Try to extract HTTP endpoints from app"""
        print(f"\n🌐 Searching for HTTP Endpoints...")
        
        api_dir = self.app_path / "Unitree_Explore" / "smali_classes3" / "com" / "unitree"
        if not api_dir.exists():
            print(f"  ⚠️  API directory not found")
            return
        
        endpoints = set()
        
        for smali_file in api_dir.rglob("*.smali"):
            try:
                content = smali_file.read_text(encoding='utf-8', errors='ignore')
                
                # Look for URL patterns
                for line in content.split('\n'):
                    if 'http' in line.lower() or '/api' in line.lower():
                        # Extract potential endpoints
                        if '"' in line:
                            parts = line.split('"')
                            for i, part in enumerate(parts):
                                if '/api' in part or 'http' in part:
                                    endpoints.add(part)
            except:
                pass
        
        if endpoints:
            print(f"\n  Found {len(endpoints)} potential endpoints:")
            for ep in sorted(endpoints)[:10]:
                print(f"    • {ep}")
        else:
            print(f"  No obvious HTTP endpoints found")

def main():
    print("\n" + "=" * 70)
    print("🎓 TEACH MODE PROTOCOL ANALYSIS")
    print("=" * 70)
    
    # Analyze PCAP
    pcap_path = Path("C:/Unitree/G1/Unitree-bot/android_app_decompiled/Unitree_Explore1/PCAPdroid_26_Jan_10_28_24.pcap")
    app_path = Path("C:/Unitree/G1/Unitree-bot/android_app_decompiled")
    
    print(f"\n📂 PCAP File: {pcap_path.name}")
    print(f"   Size: {pcap_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    parser = SimplePcapParser(pcap_path)
    if parser.parse():
        parser.print_results()
    
    # Search app
    searcher = AppSearcher(app_path)
    keywords = [
        "teach",
        "recordaction",
        "customaction", 
        "executeaction",
        "actionlist",
        "api/teach",
        "api/action",
        "api/gesture",
    ]
    searcher.search(keywords)
    searcher.extract_http_endpoints()
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)
    
    print(f"\n💡 NEXT STEPS:")
    print(f"  1. If teach mode APIs found → extract exact message format")
    print(f"  2. If no APIs found → likely HTTP/WebSocket based")
    print(f"  3. Search web_server.py for /api/teach or /api/action endpoints")
    print(f"  4. Check if teach mode is handled differently from DDS SDK")

if __name__ == "__main__":
    main()
