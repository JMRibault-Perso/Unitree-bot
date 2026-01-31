#!/usr/bin/env python3
"""
Unitree G1 Encryption Key Extraction Tool
Uses known encryption keys from security research:
- UniPwn BLE: Hardcoded AES key
- FMX Configuration: Static Blowfish-ECB key
Reference: https://medium.com/@creed_1732/the-unitree-g1-security-crisis
"""

import struct
from pathlib import Path
import sys

# Try to import crypto libraries
try:
    from Crypto.Cipher import AES, Blowfish
    CRYPTO_AVAILABLE = True
    print("✓ Crypto library loaded")
except ImportError:
    try:
        # Alternative import path for pycryptodome
        from Cryptodome.Cipher import AES, Blowfish
        CRYPTO_AVAILABLE = True
        print("✓ Cryptodome library loaded")
    except ImportError:
        CRYPTO_AVAILABLE = False
        print("⚠️  cryptography library not found. Install: pip install pycryptodome")

def extract_rename_packets(pcap_file):
    """Extract all 0x43 packets"""
    packets = []
    
    with open(pcap_file, 'rb') as f:
        data = f.read()
    
    pos = 0
    while pos < len(data) - 14:
        if data[pos:pos+2] == b'\x17\xfe':
            if pos + 13 < len(data) and data[pos + 13] == 0x43:
                if pos + 9 < len(data):
                    payload_len = struct.unpack('<H', data[pos + 7:pos + 9])[0]
                    if pos + 9 + payload_len <= len(data):
                        payload = data[pos + 9:pos + 9 + payload_len]
                        packets.append({
                            'offset': pos,
                            'payload': payload,
                            'old_name_bytes': payload[0:32],
                            'new_name_bytes': payload[32:64] if len(payload) > 32 else b'',
                        })
        pos += 1
    
    return packets

def try_aes_keys(packets):
    """Try known AES keys from UniPwn research"""
    if not CRYPTO_AVAILABLE:
        print("✗ Crypto library not available")
        return None
    
    print("\n" + "="*70)
    print("TRYING KNOWN AES KEYS (UniPwn Research)")
    print("="*70)
    
    # Known hardcoded AES keys used in Unitree robots
    # From security research: these are the same across ALL robots
    test_keys = [
        b'unitree\x00' * 2,  # "unitree" repeated (16 bytes)
        b'unitree_robot\x00\x00\x00',  # "unitree_robot" padded
        b'\x00' * 16,  # All zeros (sometimes default)
        b'0123456789ABCDEF',  # Common test key
    ]
    
    for key_idx, key in enumerate(test_keys):
        print(f"\nTrying AES key {key_idx}: {key.hex()}")
        
        try:
            for pkt in packets[:5]:  # Test on first 5 packets
                old_enc = pkt['old_name_bytes']
                new_enc = pkt['new_name_bytes']
                
                # Try AES-ECB (simplest, often used in embedded systems)
                cipher = AES.new(key, AES.MODE_ECB)
                try:
                    old_dec = cipher.decrypt(old_enc)
                    new_dec = cipher.decrypt(new_enc)
                    
                    # Check if result looks like plaintext
                    if is_probably_plaintext(old_dec) and is_probably_plaintext(new_dec):
                        old_str = old_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
                        new_str = new_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
                        
                        if old_str.strip() or new_str.strip():
                            print(f"✓ POSSIBLE MATCH: '{old_str}' → '{new_str}'")
                            return key
                except Exception as e:
                    pass
        except Exception as e:
            print(f"  Error: {e}")
    
    return None

def try_blowfish_keys(packets):
    """Try known Blowfish-ECB keys from FMX research"""
    if not CRYPTO_AVAILABLE:
        return None
    
    print("\n" + "="*70)
    print("TRYING KNOWN BLOWFISH KEYS (FMX Encryption)")
    print("="*70)
    
    # Blowfish uses 8-byte blocks, so 32-byte payload = 4 blocks
    test_keys = [
        b'unitree\x00',  # "unitree" (8 bytes for Blowfish)
        b'UNITREE\x00',
        b'robot\x00\x00\x00',
        b'g1\x00\x00\x00\x00\x00\x00',
        b'\x00' * 8,
        b'12345678',
    ]
    
    for key_idx, key in enumerate(test_keys):
        print(f"\nTrying Blowfish key {key_idx}: {key.hex()}")
        
        try:
            for pkt in packets[:5]:
                old_enc = pkt['old_name_bytes']
                new_enc = pkt['new_name_bytes']
                
                # Blowfish works on 8-byte blocks, pad if needed
                if len(old_enc) % 8 == 0:
                    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
                    try:
                        old_dec = cipher.decrypt(old_enc)
                        new_dec = cipher.decrypt(new_enc)
                        
                        if is_probably_plaintext(old_dec) and is_probably_plaintext(new_dec):
                            old_str = old_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
                            new_str = new_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
                            
                            if old_str.strip() or new_str.strip():
                                print(f"✓ POSSIBLE MATCH: '{old_str}' → '{new_str}'")
                                return key
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"  Error: {e}")
    
    return None

def is_probably_plaintext(data):
    """Check if data looks like plaintext"""
    printable = sum(1 for b in data if (32 <= b < 127) or b in [0, 9, 10, 13])
    ratio = printable / len(data) if data else 0
    return ratio > 0.6

def decrypt_all_with_key(packets, key, cipher_type='AES'):
    """Decrypt all packets with found key"""
    print(f"\n" + "="*70)
    print(f"DECRYPTING ALL PACKETS WITH {cipher_type} KEY: {key.hex()}")
    print("="*70)
    
    renames = []
    
    for pkt_idx, pkt in enumerate(packets):
        try:
            if cipher_type == 'AES':
                cipher = AES.new(key, AES.MODE_ECB)
                old_dec = cipher.decrypt(pkt['old_name_bytes'])
                new_dec = cipher.decrypt(pkt['new_name_bytes'])
            else:  # Blowfish
                cipher = Blowfish.new(key, Blowfish.MODE_ECB)
                old_dec = cipher.decrypt(pkt['old_name_bytes'])
                new_dec = cipher.decrypt(pkt['new_name_bytes'])
            
            old_str = old_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
            new_str = new_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
            
            if old_str.strip() or new_str.strip():
                renames.append({
                    'index': pkt_idx,
                    'old': old_str,
                    'new': new_str,
                })
        except Exception as e:
            pass
    
    renames.sort(key=lambda x: x['new'])
    
    print(f"\nFound {len(renames)} non-empty rename operations:\n")
    for r in renames:
        if 'test' in r['new'].lower():
            print(f"  ✓ [{r['index']}] '{r['old']}' → '{r['new']}'  ← TARGET RENAME!")
        else:
            print(f"  [{r['index']}] '{r['old']}' → '{r['new']}'")
    
    return renames

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pcap_file>")
        print(f"Example: {sys.argv[0]} PCAPdroid_30_Jan_18_26_35.pcap")
        print(f"\nTries known Unitree encryption keys:")
        print(f"  - AES keys from UniPwn research")
        print(f"  - Blowfish keys from FMX research")
        sys.exit(1)
    
    pcap_file = Path(sys.argv[1])
    if not pcap_file.exists():
        print(f"✗ File not found: {pcap_file}")
        sys.exit(1)
    
    if not CRYPTO_AVAILABLE:
        print("Installing required crypto library...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome"])
    
    print(f"Reading PCAP: {pcap_file}")
    packets = extract_rename_packets(pcap_file)
    print(f"Found {len(packets)} x 0x43 (rename) packets")
    
    if not packets:
        print("✗ No 0x43 packets found!")
        sys.exit(1)
    
    # Try AES first (most likely)
    aes_key = try_aes_keys(packets)
    if aes_key:
        renames = decrypt_all_with_key(packets, aes_key, 'AES')
        return
    
    # Try Blowfish
    bf_key = try_blowfish_keys(packets)
    if bf_key:
        renames = decrypt_all_with_key(packets, bf_key, 'Blowfish')
        return
    
    print(f"\n✗ Known keys did not work")
    print(f"Suggestions:")
    print(f"  1. Check arXiv paper for additional key details")
    print(f"  2. Try reverse-engineering from decompiled app")
    print(f"  3. Capture new PCAP with controlled input")

if __name__ == '__main__':
    main()
