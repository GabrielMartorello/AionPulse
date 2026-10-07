# SPDX-License-Identifier: GPL-3.0-only
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import Preferences
from identity_cache import IdentityCache
from protocol import Hit
from stats import Encounter
from support import Heal


class RefactorTests(unittest.TestCase):
    def test_incremental_rates_match_window_reference(self):
        encounter = Encounter()
        events = []
        for i in range(240):
            timestamp = i / 20
            actor = i % 6 + 1
            encounter.add(Hit(actor, 99, 1, i + 1), timestamp)
            encounter.add_heal(Heal(actor, actor, 17100001, i + 3), timestamp)
            events.extend(
                ((timestamp, actor, "damage", i + 1), (timestamp, actor, "healing", i + 3))
            )
            for kind in ("damage", "healing"):
                expected = {}
                for stamp, entity, metric, amount in events:
                    if timestamp - 5 < stamp <= timestamp and metric == kind:
                        expected[entity] = expected.get(entity, 0) + amount / 5
                actual = encounter.current_rate(timestamp, kind)
                self.assertEqual(set(actual), set(expected))
                for entity, value in expected.items():
                    self.assertAlmostEqual(actual[entity], value)
        self.assertEqual(encounter.current_rate(20, "damage"), {})
        self.assertEqual(encounter.current_rate(20, "healing"), {})

    def test_future_events_do_not_enter_current_rate(self):
        encounter = Encounter()
        encounter.add(Hit(1, 99, 1, 100), 10)
        encounter.add(Hit(2, 99, 1, 200), 12)
        self.assertEqual(encounter.current_rate(11), {1: 20})
        self.assertEqual(encounter.current_rate(12), {1: 20, 2: 40})

    def test_identity_restore_reads_once_and_respects_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = IdentityCache(Path(directory) / "cache.json")
            cache.save("a", {1: "Player", 2: "Healer"}, now=100, self_id=1, group={1, 2})
            original = Path.read_text
            with patch.object(Path, "read_text", autospec=True, side_effect=original) as read:
                self.assertEqual(cache.restore("a", 101), ({1: "Player", 2: "Healer"}, 1, {1, 2}))
                self.assertEqual(read.call_count, 1)
            self.assertEqual(cache.restore("b", 101), ({}, None, set()))

    def test_preferences_atomic_and_unchanged_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "preferences.json"
            preferences = Preferences(path)
            preferences.update(overlay_x=120, overlay_y=200)
            self.assertEqual(Preferences(path).values, {"overlay_x": 120, "overlay_y": 200})
            with patch.object(Path, "write_text") as write:
                preferences.update(overlay_x=120)
                write.assert_not_called()
            self.assertFalse(path.with_suffix(".tmp").exists())
