# SPDX-License-Identifier: GPL-3.0-only
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / "vendor")]
import struct
import unittest
import lz4.block
from protocol import varint, damage_events, Framer, TcpStream, Hit, nickname
from stats import Encounter


def encode(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def frame(payload, outer_bundle=False):
    size = len(payload) + 1 + 3 - int(outer_bundle)
    while True:
        prefix = encode(size)
        updated = len(payload) + len(prefix) + 3 - int(outer_bundle)
        if size == updated:
            return prefix + payload
        size = updated


def direct(damage=500, shifted=False, actor=42):
    data = b"\x04\x38\x01\x00" + encode(100) + encode(4) + encode(0) + encode(actor)
    data += struct.pack("<I", 10_010_001) + b"\x00" + encode(3) + bytes(8)
    tail = encode(0) + encode(777) + encode(damage) if shifted else encode(1) + encode(damage)
    return data + tail + encode(2) + encode(250) + encode(250)


class ProtocolTests(unittest.TestCase):
    def test_varint_boundaries(self):
        for value in (0, 127, 128, 16384, 2**32 - 1):
            self.assertEqual(varint(encode(value)), (value, len(encode(value))))
        for value in (b"\x80", b"\x80" * 5, b"\xff" * 5):
            with self.assertRaises(ValueError):
                varint(value)

    def test_damage_old_and_shifted_not_double_counted(self):
        for shifted in (False, True):
            hit = damage_events(direct(shifted=shifted))[0]
            self.assertEqual((hit.actor, hit.damage, hit.critical), (42, 500, True))

    def test_dot(self):
        data = b"\x05\x38" + encode(100) + b"\x02" + encode(42) + encode(0)
        data += struct.pack("<I", 10_010_001) + encode(123)
        hits = damage_events(data)
        self.assertEqual((hits[0].damage, hits[0].dot), (123, True))

    def test_malformed_record_has_no_hit(self):
        source = direct()

        for end in range(0, len(source) - 6):
            self.assertEqual(damage_events(source[:end]), [])
        self.assertEqual(damage_events(b"\x99\x99" + source), [])

    def test_fragmented_coalesced_and_extension(self):
        seen = []
        data = frame(direct()) + frame(b"\xf1" + direct(actor=43))
        parser = Framer(seen.append)
        for byte in data:
            parser.feed(bytes([byte]))
        self.assertEqual([damage_events(p)[0].actor for p in seen], [42, 43])
        self.assertEqual(parser.buffer, b"")

    def test_compressed_bundle(self):
        raw = frame(direct()) + frame(direct(actor=43))
        payload = (
            b"\xff\xff" + struct.pack("<I", len(raw)) + lz4.block.compress(raw, store_size=False)
        )
        seen = []
        parser = Framer(seen.append)
        wire = frame(payload, outer_bundle=True)
        parser.feed(wire[:4])
        parser.feed(wire[4:])
        self.assertEqual([damage_events(p)[0].actor for p in seen], [42, 43])

    def test_tcp_reorder_duplicate_overlap_wrap(self):
        data = frame(direct())
        seen = []
        stream = TcpStream(seen.append)
        origin = 2**32 - 7
        stream.feed(origin, data[:3])
        stream.feed((origin + 10) % 2**32, data[10:])
        stream.feed((origin + 2) % 2**32, data[2:10])
        stream.feed(origin, data)
        self.assertEqual(len(seen), 1)
        self.assertEqual(damage_events(seen[0])[0].damage, 500)

    def test_corrupt_lz4_bundle_does_not_stop_capture(self):
        seen = []
        parser = Framer(seen.append)
        invalid = b"\xff\xff" + struct.pack("<I", 100) + b"\xff\xff\xff"
        parser.feed(frame(invalid, outer_bundle=True) + frame(direct()))
        self.assertEqual(parser.errors, 1)
        self.assertEqual(len(seen), 1)
        self.assertEqual(damage_events(seen[0])[0].damage, 500)

    def test_name_and_me(self):
        name = b"Gabriel"
        payload = b"\x33\x36" + encode(42) + bytes(5) + bytes([len(name)]) + name + b"\x01\x00"
        self.assertEqual(nickname(payload), (42, "Gabriel", True))
        self.assertIsNone(nickname(payload[:-3]))

    def test_name_with_null_terminator(self):
        name = b"TestPlayer\x00"
        payload = b"\x33\x36" + encode(42) + bytes(5) + bytes([len(name)]) + name + b"\x01\x00"
        self.assertEqual(nickname(payload), (42, "TestPlayer", True))

    def test_sa_entity_name_maps_to_owner_not_summon(self):

        for prefix in ("048de1f0036005b800da5164090a", "048de4ec0340b7b700da5164090a"):
            payload = bytes.fromhex(prefix) + b"TestPlayer" + b"\x00\x00"
            self.assertEqual(nickname(payload), (10458, "TestPlayer", False))
            self.assertIsNone(nickname(payload[:20]))

    def test_sa_entity_ownership_only_has_no_invented_name(self):
        payload = b"\x04\x8d" + encode(1000) + bytes(4) + encode(42)
        self.assertIsNone(nickname(payload))

    def test_group_duration_freezes_after_idle(self):
        stats = Encounter()
        stats.add(Hit(42, 100, 1, 500), 100)
        stats.add(Hit(43, 100, 1, 500), 105)
        self.assertEqual(stats.duration(106), 6)
        self.assertEqual(stats.duration(120), 5)
        self.assertEqual(stats.rows(120, {42})[0][2], 500)
        self.assertEqual(stats.duration(120, {42, 43}), 5)
        self.assertEqual(len(stats.rows(120, {42})), 1)
        stats.clear()
        self.assertEqual(stats.rows(120), [])


if __name__ == "__main__":
    unittest.main()
