# SPDX-License-Identifier: GPL-3.0-only
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from region import detect_region


class RegionTests(unittest.TestCase):
    def test_known_connected_addresses(self):
        self.assertEqual(detect_region(bytes((193, 202, 112, 174))), "América do Sul")
        self.assertEqual(detect_region("193.202.112.191"), "América do Sul")
        self.assertEqual(detect_region("206.127.156.40"), "Coreia")

    def test_unknown_hosts_are_not_guessed_from_neighboring_ips(self):
        for address in ("193.202.112.192", "1.2.3.4", "::1", "invalid"):
            self.assertEqual(detect_region(address), "não identificada")
