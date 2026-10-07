# SPDX-License-Identifier: GPL-3.0-only
import unittest
from party import party_members, party_snapshot, party_roster, resolve_party_roster


class PartyTests(unittest.TestCase):
    def row(self):
        body = bytearray(150)
        body[0:2] = b"\x03\x02"
        body[2:6] = (5515).to_bytes(4, "little")
        body[6:8] = body[53:55] = (1001).to_bytes(2, "little")
        body[10] = 36
        body[11:47] = b"12345678-1234-1234-1234-123456789abc"
        body[55] = 5
        body[56:61] = b"Amigo"
        return body

    def test_join_without_damage(self):
        self.assertEqual(party_members(b"\x0d\x92" + self.row()), [(5515, "Amigo", 2)])

    def test_join_with_zero_profile_state_without_damage(self):
        row = self.row()
        row[0] = 0
        self.assertEqual(party_members(b"\x0d\x92" + row), [(5515, "Amigo", 2)])
        row[2:6] = bytes(4)
        self.assertEqual(party_members(b"\x0d\x92" + row), [])

    def test_join_still_validates_zero_state_profile(self):
        row = self.row()
        row[0] = 0
        row[11] = 0
        self.assertEqual(party_members(b"\x0d\x92" + row), [])

    def test_invalid_and_nearby_do_not_join(self):
        row = self.row()
        row[53] = 0
        self.assertEqual(party_members(b"\x0d\x92" + row), [])
        self.assertEqual(party_members(b"\x33\x36" + self.row()), [])
        for size in range(61):
            self.assertEqual(party_members(b"\x0d\x92" + self.row()[:size]), [])

    def test_status(self):
        self.assertEqual(party_members(b"\x1b\x92\x01\x05\x0a" + bytes(25)), [(1, "", 0)])
        self.assertEqual(party_members(b"\x1b\x92\x01\x0b\x0a" + bytes(25)), [])

    def snapshot(self):
        row = self.row()
        listed = b"\x01" + row
        return b"\x00\x92" + bytes(25) + listed

    def test_complete_roster(self):
        self.assertEqual(party_snapshot(self.snapshot()), [(5515, "Amigo", 2)])

    def test_partial_roster_cannot_remove_members(self):
        self.assertIsNone(party_snapshot(self.snapshot()[:-2]))
        self.assertIsNone(party_snapshot(b"\x00\x92" + bytes(25)))

    def test_unresolved_profile_cannot_remove_members(self):
        packet = bytearray(self.snapshot())
        packet[30:34] = bytes(4)
        self.assertIsNone(party_snapshot(packet))

    def test_profile_only_snapshot_resolves_unique_identity(self):
        packet = bytearray(self.snapshot())
        packet[30:34] = bytes(4)
        roster = party_roster(packet)
        self.assertEqual(roster, [(0, "Amigo", 2)])
        self.assertEqual(resolve_party_roster(roster, {5515: "Amigo"}, 5515), [(5515, "Amigo", 2)])
        self.assertIsNone(resolve_party_roster(roster, {5515: "Amigo", 99: "Amigo"}, 5515))
        self.assertIsNone(resolve_party_roster(roster, {}, 5515))
        self.assertIsNone(party_roster(packet[:-2]))

    def test_snapshot_requires_self_before_removal(self):
        self.assertIsNone(resolve_party_roster([(5515, "Amigo", 2)], {1: "Eu"}, 1))
        self.assertIsNone(resolve_party_roster([(0, "Amigo", 2)], {5515: "Amigo"}, None))
