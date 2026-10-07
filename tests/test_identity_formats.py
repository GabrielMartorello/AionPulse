# SPDX-License-Identifier: GPL-3.0-only
import queue
import struct
import unittest

from capture import Capture
from party import party_roster, resolve_party_roster
from protocol import identity_records


def encode(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    return bytes(result + bytes([value]))


def identity(actor, name, opcode=b"\x45\x36", gate=7):
    raw = name.encode("utf-8")
    return opcode + encode(actor) + bytes(4) + bytes([gate, len(raw)]) + raw


def member(slot, name, variable=0):
    raw = name.encode("utf-8")
    dbid = (1001 << 48) | slot
    return (
        bytes([1, slot])
        + struct.pack("<Q", dbid)
        + bytes([len(raw)])
        + raw
        + struct.pack("<III", 1, 30, 100)
        + bytes(variable)
        + struct.pack("<HHBQ", 1001, 0, 4, 2000)
        + bytes(3)
    )


def roster(records, count=None):
    header = b"\x02\x97" + struct.pack("<I", 123) + b"\x05Group\x06"
    header += struct.pack("<I", 600091) + bytes(13) + encode(count or len(records))
    return header + b"".join(records)


class IdentityFormatTests(unittest.TestCase):
    def test_mask_variants_unicode_single_character_and_old_opcode(self):
        for gate in (1, 7, 0x37, 0x81):
            for opcode in (b"\x33\x36", b"\x44\x36", b"\x45\x36"):
                records = identity_records(identity(123456, "月", opcode, gate))
                self.assertEqual(records[0][0], (123456, "月", opcode == b"\x33\x36"))

    def test_embedded_multiple_names_reach_capture_without_combat(self):
        events = queue.Queue()
        capture = Capture(events)
        payload = b"\x99\x99prefix" + identity(42, "Player", b"\x33\x36")
        payload += b"tail" + identity(43, "Healer")
        capture.parse(payload)
        self.assertEqual(
            [events.get_nowait(), events.get_nowait()],
            [("name", (42, "Player", True)), ("name", (43, "Healer", False))],
        )
        self.assertTrue(events.empty())

    def test_invalid_and_truncated_embedded_records_are_rejected(self):
        packet = identity(42, "Healer")
        for end in range(len(packet)):
            self.assertEqual(identity_records(b"\x99\x99" + packet[:end]), [])
        for name in ("1234", "Bad name", "Bad\x00Name", "A" * 13):
            self.assertEqual(identity_records(b"\x99\x99" + identity(42, name)), [])
        self.assertEqual(identity_records(b"\x99\x99" + identity(42, "Healer", gate=2)), [])

    def test_conflicting_actors_and_multiple_self_records_are_not_bound(self):
        self.assertEqual(identity_records(identity(42, "One") + identity(42, "Two")), [])
        self.assertEqual(
            identity_records(identity(42, "One", b"\x33\x36") + identity(43, "Two", b"\x33\x36")),
            [],
        )

    def test_named_party_roster_variable_tail_and_unique_actor_resolution(self):
        packet = roster([member(1, "Player", 1), member(2, "Healer", 3)])
        rows = [(0, "Player", 1), (0, "Healer", 2)]
        self.assertEqual(party_roster(packet), rows)
        self.assertEqual(
            resolve_party_roster(rows, {42: "Player", 43: "Healer"}, 42),
            [(42, "Player", 1), (43, "Healer", 2)],
        )
        self.assertIsNone(resolve_party_roster(rows, {42: "Player"}, 42))
        self.assertIsNone(
            resolve_party_roster(rows, {42: "Player", 43: "Healer", 44: "Healer"}, 42)
        )

    def test_partial_roster_does_not_remove_members(self):
        packet = roster([member(1, "Player"), member(2, "Healer")])
        for end in range(len(packet) - 3):
            self.assertIsNone(party_roster(packet[:end]))
        self.assertIsNone(party_roster(roster([member(1, "Player"), member(2, "Player")])))

    def test_vacant_slot_finishes_complete_roster(self):
        vacant = bytes([0, 2]) + bytes(9)
        self.assertEqual(party_roster(roster([member(1, "Player"), vacant])), [(0, "Player", 1)])
