#!/usr/bin/env python3
"""
Extract action list (0x1A response) and inspect play action (0x41) payloads
from a PCAP file. This is passive analysis only.
"""
import struct
import sys
from binascii import hexlify

MAGIC = b"\x17\xfe\xfd"


def iter_packets(pcap_path):
    with open(pcap_path, "rb") as f:
        f.read(24)  # global header
        while True:
            hdr = f.read(16)
            if len(hdr) < 16:
                break
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", hdr)
            data = f.read(incl_len)
            yield ts_sec + ts_usec / 1_000_000.0, data


def find_protocol_frames(data):
    frames = []
    # Find all occurrences of magic header
    start = 0
    while True:
        idx = data.find(MAGIC, start)
        if idx == -1:
            break
        # need at least header bytes
        if len(data) >= idx + 15:
            frames.append(idx)
        start = idx + 1
    return frames


def parse_action_list(frame):
    # frame points to 0x17 fe fd
    # Observed layout: cmd at offset 13
    if len(frame) < 20:
        return None
    cmd = frame[13]
    if cmd != 0x1A:
        return None
    payload_len = int.from_bytes(frame[14:16], "big")
    action_count = int.from_bytes(frame[16:18], "big")
    # Sanity checks to avoid parsing encrypted DTLS payloads
    if payload_len > 0x0200 or action_count == 0 or action_count > 15:
        return None
    # action data starts at offset 18
    action_data = frame[18:18 + (action_count * 36)]
    if len(action_data) < action_count * 36:
        return None
    actions = []
    for i in range(action_count):
        base = i * 36
        name_bytes = action_data[base:base + 32]
        try:
            name = name_bytes.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
        except Exception:
            name = name_bytes.hex()
        meta = action_data[base + 32:base + 36]
        actions.append({"index": i + 1, "name": name, "meta": meta.hex()})
    return {
        "payload_len": payload_len,
        "action_count": action_count,
        "actions": actions,
    }


def parse_play_packet(frame):
    if len(frame) < 24:
        return None
    cmd = frame[13]
    if cmd != 0x41:
        return None
    payload_len = int.from_bytes(frame[14:16], "big")
    # Sanity check: play packets are typically < 256 bytes in raw UDP captures
    if payload_len > 0x0200 or payload_len < 1:
        return None
    payload = frame[16:16 + payload_len]
    if len(payload) < payload_len:
        return None
    return {
        "payload_len": payload_len,
        "payload_hex": hexlify(payload[:64]).decode(),
        "payload": payload,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_actions_and_play_payloads.py <pcap>")
        return 1

    pcap_path = sys.argv[1]
    action_lists = []
    play_packets = []

    for ts, data in iter_packets(pcap_path):
        for idx in find_protocol_frames(data):
            frame = data[idx:]
            action_list = parse_action_list(frame)
            if action_list:
                action_lists.append((ts, action_list))
                continue
            play = parse_play_packet(frame)
            if play:
                play_packets.append((ts, play))

    print("=" * 72)
    print(f"PCAP: {pcap_path}")
    print(f"Found action list responses: {len(action_lists)}")
    print(f"Found play action packets (0x41): {len(play_packets)}")
    print("=" * 72)

    if action_lists:
        ts, action_list = action_lists[-1]
        print(f"\nLATEST ACTION LIST @ {ts}")
        print(f"Payload length: {action_list['payload_len']}")
        print(f"Action count: {action_list['action_count']}")
        for action in action_list["actions"]:
            print(f"  {action['index']:>2}. {action['name']} (meta={action['meta']})")

    if play_packets:
        print("\nPLAY PACKET PAYLOAD PREVIEW (first 64 bytes)")
        for i, (ts, play) in enumerate(play_packets[:5], 1):
            print(f"  #{i} @ {ts} len={play['payload_len']} hex={play['payload_hex']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
