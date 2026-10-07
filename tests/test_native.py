# SPDX-License-Identifier: GPL-3.0-only
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from native import tcp_payload


def ipv4_packet(payload=b"abc", fragment=0):
    tcp = struct.pack("!HHII", 13328, 40000, 123, 0) + bytes([0x50, 0x18]) + bytes(6) + payload
    ip = bytes([0x45, 0]) + struct.pack("!HHH", 20 + len(tcp), 0, fragment)
    ip += bytes([64, 6]) + bytes(2) + bytes([1, 2, 3, 4, 192, 168, 0, 23])
    return bytes(12) + b"\x08\x00" + ip + tcp


class NativeTests(unittest.TestCase):
    def test_ethernet_and_vlan(self):
        raw = ipv4_packet()
        vlan = raw[:12] + b"\x81\x00\x00\x01\x08\x00" + raw[14:]
        for data in (raw, vlan):
            key, seq, flags, payload = tcp_payload(data, 1)
            self.assertEqual((key[2], key[3], seq, payload), (13328, 40000, 123, b"abc"))

    def test_truncated_and_fragmented_rejected(self):
        raw = ipv4_packet()
        for length in range(len(raw)):
            self.assertIsNone(tcp_payload(raw[:length], 1))
        self.assertIsNone(tcp_payload(ipv4_packet(fragment=0x2000), 1))
        self.assertIsNone(tcp_payload(ipv4_packet(fragment=1), 1))

    def test_loopback(self):
        raw = struct.pack("<I", 2) + ipv4_packet()[14:]
        self.assertEqual(tcp_payload(raw, 0)[-1], b"abc")

    def test_ipv6(self):
        tcp = struct.pack("!HHII", 13328, 40000, 123, 0) + bytes([0x50, 0x18]) + bytes(6) + b"abc"
        ip = b"\x60\x00\x00\x00" + struct.pack("!H", len(tcp)) + b"\x06\x40" + bytes(32)
        raw = bytes(12) + b"\x86\xdd" + ip + tcp
        self.assertEqual(tcp_payload(raw, 1)[-1], b"abc")


if __name__ == "__main__":
    unittest.main()
