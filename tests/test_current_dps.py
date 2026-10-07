# SPDX-License-Identifier: GPL-3.0-only
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from protocol import Hit
from stats import Encounter


class CurrentDpsTests(unittest.TestCase):
    def test_window_and_idle_preserve_total(self):
        encounter = Encounter()
        encounter.add(Hit(1, 99, 10, 500), 100)
        encounter.add(Hit(1, 99, 10, 1000), 103)
        self.assertEqual(encounter.current_dps(104), {1: 300})
        self.assertEqual(encounter.current_dps(105), {1: 200})
        self.assertEqual(encounter.current_dps(108), {})
        self.assertEqual(encounter.rows(108)[0][1], 1500)
        self.assertEqual(len(encounter.recent), 0)

    def test_players_and_reset(self):
        encounter = Encounter()
        encounter.add(Hit(1, 99, 10, 500), 100)
        encounter.add(Hit(2, 99, 10, 1000), 101)
        self.assertEqual(encounter.current_dps(102), {1: 100, 2: 200})
        encounter.clear()
        self.assertEqual(encounter.current_dps(102), {})
        self.assertEqual(encounter.rows(102), [])
