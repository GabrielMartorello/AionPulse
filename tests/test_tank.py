# SPDX-License-Identifier: GPL-3.0-only
import struct
import unittest
from test_support import encode, packet
from tank import TankParser
from stats import Encounter
from protocol import Hit
from tank import TankEvent


def pool(mode, actor, amount, emitted=None, chain=42, target=1):
    tail = (encode(emitted) if emitted is not None else b"") + struct.pack("<I", 12230001)
    return (
        b"\x05\x38"
        + encode(target)
        + encode(mode)
        + encode(actor)
        + encode(chain)
        + struct.pack("<I", 123)
        + encode(amount)
        + tail
    )


class TankTests(unittest.TestCase):
    def test_received_includes_hp_absorption_and_quantified_reduction(self):
        stats = Encounter()
        stats.add_received(Hit(99, 1, 1217120, 300), 10)
        stats.add_tank(TankEvent(1, 12230001, "absorbed", 400, 2), 10)
        stats.add_tank(TankEvent(1, 1217120, "defenses", 1, 99, ("block",)), 10)
        self.assertEqual(stats.players[1]["health_received"], 300)
        self.assertEqual(stats.players[1]["received"], 700)
        self.assertEqual(stats.current_rate(11, "received"), {1: 140})
        self.assertEqual(stats.rows(11, {1}, "received")[0][1], 700)

        stats.add_tank(TankEvent(1, 1217120, "mitigated", 200, 99), 11)
        self.assertEqual(stats.players[1]["received"], 900)
        self.assertEqual(stats.players[1]["damage"], 0)
        self.assertEqual(stats.players[1]["healing"], 0)
        stats.clear()
        self.assertFalse(stats.players)

    def test_grant_is_not_absorption_and_expiration_is_not_damage(self):
        parser = TankParser()
        self.assertEqual(parser.parse(pool(9, 2, 1000)), ([], True))
        self.assertEqual(parser.parse(pool(10, 2, 0)), ([], True))
        self.assertEqual(parser.parse(pool(11, 99, 600, 400)), ([], False))

    def test_actual_consumption_target_credit_and_no_duplicate_grant(self):
        parser = TankParser()
        parser.parse(pool(9, 2, 1000))
        events, consumed = parser.parse(pool(11, 99, 600, 400))
        self.assertTrue(consumed)
        stats = Encounter()
        for event in events:
            stats.add_tank(event, 10)
        self.assertEqual(stats.players[1]["absorbed"], 400)
        self.assertEqual(stats.players[1]["shield_granted"], 1000)
        self.assertEqual(stats.players[1]["received"], 400)
        self.assertEqual(stats.players[1]["healing"], 0)
        events, _ = parser.parse(pool(11, 99, 500, 100))
        for event in events:
            stats.add_tank(event, 11)
        self.assertEqual(stats.players[1]["absorbed"], 500)
        self.assertEqual(stats.players[1]["received"], 500)
        self.assertEqual(stats.players[1]["shield_granted"], 1000)
        self.assertEqual(stats.current_rate(12, "absorbed"), {1: 100})
        self.assertEqual(stats.current_rate(16, "absorbed"), {})

    def test_recovery_pool_and_connection_reset(self):
        parser = TankParser()
        parser.parse(pool(9, 2, 1000))
        self.assertEqual(parser.parse(pool(11, 2, 600, 400)), ([], False))
        parser.clear()
        self.assertEqual(parser.parse(pool(11, 99, 600, 400)), ([], False))

    def test_defensive_flags_only_and_count_not_damage(self):
        parser = TankParser()
        raw = packet(99, 1, 1217120, 300, layout=6, detail=b"\x03" + bytes(9))
        self.assertEqual(parser.parse(raw), ([], False))

        raw = raw[:3] + b"\x46\x10" + raw[5:]
        events, _ = parser.parse(raw)
        self.assertEqual(events[0].defenses, ("block", "parry"))
        stats = Encounter()
        stats.add_tank(events[0], 10)
        self.assertEqual(stats.players[1]["defenses"], 1)
        self.assertEqual(stats.players[1]["block"], 1)
        self.assertEqual(stats.players[1]["parry"], 1)
        self.assertEqual(stats.players[1]["absorbed"], 0)

    def test_truncated_absorption_is_ignored(self):
        parser = TankParser()
        parser.parse(pool(9, 2, 1000))
        raw = pool(11, 99, 600, 400)
        for size in range(2, 9):
            self.assertEqual(parser.parse(raw[:size]), ([], False))


if __name__ == "__main__":
    unittest.main()
