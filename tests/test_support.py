# SPDX-License-Identifier: GPL-3.0-only
import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from support import Heal, support_events
from stats import Encounter


def encode(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def packet(actor, target, skill, amount, layout=4, detail=None, unknown=1, loop=1):
    size = {4: 8, 6: 10}[layout]
    return (
        b"\x04\x38"
        + encode(target)
        + encode(layout)
        + b"\x00"
        + encode(actor)
        + struct.pack("<I", skill)
        + b"\x00\x02"
        + (detail or bytes(size))
        + encode(unknown)
        + encode(amount)
        + encode(loop)
        + b"\x00"
    )


class SupportTests(unittest.TestCase):
    def test_enemy_skill_and_target_accounting(self):
        incoming, healing = support_events(
            packet(30140, 10458, 1217120, 10000, layout=6, unknown=0, loop=13)
        )
        self.assertEqual(incoming[0].damage, 13)
        self.assertFalse(healing)
        stats = Encounter()
        stats.add_received(incoming[0], 10)
        self.assertEqual(stats.rows(11, {10458}, "received")[0][1], 13)
        self.assertEqual(stats.current_rate(11, "received"), {10458: 2.6})
        self.assertEqual(stats.rows(11, {10458}, "damage")[0][1], 0)

    def test_potion_is_recovery_not_dps_or_healer_credit(self):
        incoming, healing = support_events(packet(10458, 10458, 2010101, 1359))
        self.assertFalse(incoming)
        self.assertEqual(healing[0].category, "potion")
        stats = Encounter()
        stats.add_heal(healing[0], 10)
        self.assertEqual(stats.players[10458]["potion"], 1359)
        self.assertEqual(stats.rows(11, {10458}, "recovery")[0][1], 1359)
        self.assertEqual(stats.rows(11, {10458}, "healing")[0][1], 0)
        self.assertEqual(stats.rows(11, {10458}, "damage")[0][1], 0)

    def test_healer_and_recipient_are_distinct(self):
        incoming, healing = support_events(packet(2, 1, 17100001, 500))
        self.assertFalse(incoming)
        stats = Encounter()
        stats.add_heal(healing[0], 10)
        self.assertEqual(stats.players[2]["healing"], 500)
        self.assertEqual(stats.players[1]["recovery"], 500)
        self.assertEqual(stats.current_rate(15, "healing"), {})
        self.assertEqual(stats.players[2]["healing"], 500)
        stats.clear()
        self.assertFalse(stats.players)

    def test_mana_shield_and_truncation_not_healing(self):
        self.assertEqual(support_events(packet(1, 1, 12230001, 511)), ([], []))
        self.assertEqual(
            support_events(packet(1, 1, 17100001, 500, detail=b"\x58" + bytes(7))), ([], [])
        )
        p = packet(2, 1, 17100001, 500)
        for length in range(len(p) - 2):
            self.assertEqual(support_events(p[:length]), ([], []))

    def test_health_marker_and_periodic_recovery(self):
        self.assertEqual(
            support_events(packet(2, 1, 123, 500, detail=b"\x57" + bytes(7)))[1][0].amount, 500
        )
        p = b"\x05\x38\x01\x0b\x01\x00" + struct.pack("<I", 123) + encode(500)
        self.assertEqual(support_events(p)[1][0].amount, 500)

    def test_corroborated_self_recovery(self):
        incoming, heals = support_events(packet(1, 1, 12720001, 511))
        self.assertFalse(incoming)
        self.assertEqual(heals[0], Heal(1, 1, 12720001, 511))
