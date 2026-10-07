# SPDX-License-Identifier: GPL-3.0-only
import struct
import unittest
from party_identity import PartyIdentity, character_identity, remote_party_identity


class PartyIdentityTests(unittest.TestCase):
    def identity(self, character=123456, server=1001):
        return (
            b"\x45\x36"
            + bytes(20)
            + b"\x0e\x01\x01"
            + struct.pack("<IHHB", character, 0, server, 4)
        )

    def remote(self, character=123456, server=1001):
        body = bytearray(63)
        struct.pack_into("<IHHI", body, 0, character, 0, server, 32)
        struct.pack_into("<fff", body, 24, 100, 200, 300)
        body[-1] = 1
        return b"\x1c\x92" + body

    def test_recovers_without_own_identity_or_combat(self):
        tracker = PartyIdentity()
        self.assertEqual(tracker.observe(self.remote()), [])
        self.assertEqual(
            tracker.observe(self.identity(), (42, "Healer", False)), [(42, "Healer", 0)]
        )
        self.assertEqual(tracker.observe(self.remote()), [])

    def test_identity_before_remote_and_new_entity_id(self):
        tracker = PartyIdentity()
        self.assertEqual(tracker.observe(self.identity(), (42, "Healer", False)), [])
        self.assertEqual(tracker.observe(self.remote()), [(42, "Healer", 0)])
        self.assertEqual(
            tracker.observe(self.identity(), (43, "Healer", False)), [(43, "Healer", 0)]
        )

    def test_nearby_player_and_other_server_are_not_party(self):
        tracker = PartyIdentity()
        self.assertEqual(tracker.observe(self.identity(), (42, "Nearby", False)), [])
        self.assertEqual(tracker.observe(self.remote(server=2001)), [])
        tracker.clear()
        self.assertEqual(tracker.observe(self.remote()), [])

    def test_scene_changes_keep_emission_history_bounded(self):
        tracker = PartyIdentity()
        tracker.observe(self.remote())
        for actor in range(1, 1000):
            self.assertEqual(
                tracker.observe(self.identity(), (actor, "Healer", False)),
                [(actor, "Healer", 0)],
            )
        self.assertEqual(len(tracker.emitted), 1)

    def test_malformed_and_ambiguous_profiles_are_rejected(self):
        self.assertIsNone(character_identity(self.identity()[:-1]))
        self.assertIsNone(character_identity(self.identity() + self.identity(character=999)))
        self.assertIsNone(remote_party_identity(self.remote()[:-1]))
        self.assertIsNone(remote_party_identity(self.remote(server=0)))
        malformed = bytearray(self.remote())
        struct.pack_into("<f", malformed, 26, float("nan"))
        self.assertIsNone(remote_party_identity(malformed))
