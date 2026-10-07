# SPDX-License-Identifier: GPL-3.0-only
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from identity_cache import IdentityCache, connection_key


class IdentityCacheTests(unittest.TestCase):
    def test_partial_party_can_restore_before_names_arrive(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = IdentityCache(Path(directory) / "cache.json")
            cache.save("a", {}, now=100, group={20})
            self.assertEqual(cache.restore("a", now=200), ({}, None, {20}))
            self.assertEqual(cache.load_group("a", now=200), {20})
            self.assertEqual(cache.load_group("b", now=200), set())

    def test_confirmed_roster_persists_only_with_valid_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = IdentityCache(Path(directory) / "cache.json")
            cache.save(
                "a", {10: "TestPlayer"}, now=100, self_id=10, group={10}, roster_confirmed=True
            )
            cache.restore("a", now=200)
            self.assertTrue(cache.roster_confirmed)
            cache.restore("b", now=200)
            self.assertFalse(cache.roster_confirmed)

    def test_reopen_same_connection_and_no_fixed_party(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            IdentityCache(path).save("session-a", {10: "TestPlayer", 20: "Healer"}, now=100)
            self.assertEqual(
                IdentityCache(path).load("session-a", now=200), {10: "TestPlayer", 20: "Healer"}
            )
            self.assertEqual(IdentityCache(path).load("session-b", now=200), {})
            self.assertEqual(IdentityCache(path).load_group("session-a", now=200), set())

    def test_expired_or_broken_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            cache = IdentityCache(path)
            cache.save("a", {10: "TestPlayer"}, now=100)
            self.assertEqual(cache.load("a", now=1000), {})
            path.write_text("invalid")
            self.assertEqual(cache.load("a"), {})

    def test_connection_key_changes_with_client_port(self):
        key = (bytes([1, 2, 3, 4]), bytes([5, 6, 7, 8]), 13328, 50000)
        self.assertNotEqual(connection_key(key), connection_key((*key[:3], 50001)))

    def test_self_identity_is_explicit_and_expires(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = IdentityCache(Path(directory) / "cache.json")
            cache.save("a", {10: "Personagem do pacote"}, now=100, self_id=10)
            self.assertEqual(cache.load_self("a", now=200), 10)
            self.assertIsNone(cache.load_self("b", now=200))
            self.assertIsNone(cache.load_self("a", now=1000))

    def test_observed_party_restored_only_on_same_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = IdentityCache(Path(directory) / "cache.json")
            cache.save("a", {10: "Eu", 20: "Membro"}, now=100, self_id=10, group={10, 20})
            self.assertEqual(cache.load_group("a", now=200), {10, 20})
            self.assertEqual(cache.load_group("b", now=200), set())
            cache.save("a", {10: "Eu", 20: "Membro"}, now=200, self_id=10, group={10})
            self.assertEqual(cache.load_group("a", now=201), {10})
