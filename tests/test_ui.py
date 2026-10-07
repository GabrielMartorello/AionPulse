# SPDX-License-Identifier: GPL-3.0-only
import os
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import App
from config import Preferences
from overlay import CompactOverlay
from protocol import Hit
from tank import TankEvent
from i18n import set_language


@unittest.skipUnless(os.name == "nt", "Windows UI integration")
class UiTests(unittest.TestCase):
    def test_initial_modes_show_all_metrics(self):
        self.assertEqual(self.app.metric.get(), "all")
        self.assertEqual(self.app.overlay.metric.get(), "all")

    def test_identification_guidance_distinguishes_partial_from_observed_names(self):
        self.app.group = set()
        self.assertIn("Aguardando identificação", self.app.identification_message())
        self.app.group = {1, 2}
        self.app.me = None
        self.assertIn("Identificação parcial", self.app.identification_message())
        self.app.me = 1
        self.assertIn("integrantes observados identificados", self.app.identification_message())

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        preferences = Preferences(Path(self.directory.name) / "preferences.json")
        with (
            patch("app.Capture.interfaces", return_value=[]),
            patch("app.Preferences", return_value=preferences),
        ):
            self.app = App(self.root)
        self.app.group = {1, 2}
        self.app.me = 1
        self.app.names = {1: "Player", 2: "Healer"}
        self.app.overlay = CompactOverlay(self.app, {})

    def tearDown(self):
        self.app.quit()
        set_language("pt-BR")
        self.directory.cleanup()

    def test_language_switch_preserves_combat_and_updates_overlay(self):
        self.app.encounter.add(Hit(1, 99, 100, 12345, False), time.monotonic())
        self.app.events.put(("region", "América do Sul"))
        self.app._drain_events()
        self.app.language.set("English")
        self.app.change_language()
        self.assertEqual(self.app.preferences.values["language"], "en")
        self.assertEqual(self.app.region_text.get(), "AION2 · Region: South America")
        self.assertEqual(self.app.overlay.reset_button.cget("text"), "Reset")
        self.assertEqual(self.app.encounter.players[1]["damage"], 12345)
        self.app.language.set("Português (Brasil)")
        self.app.change_language()
        self.assertEqual(self.app.overlay.reset_button.cget("text"), "Reiniciar")
        self.assertEqual(self.app.region_text.get(), "AION2 · Região: América do Sul")

    def test_full_values_are_shared_and_persisted(self):
        self.assertEqual(self.app.display_number(12345), "12.3k")
        self.app.full_values.set(True)
        self.assertEqual(self.app.display_number(12345), "12.345")
        self.assertTrue(self.app.preferences.values["full_values"])
        self.app.language.set("English")
        self.app.change_language()
        self.assertEqual(self.app.display_number(12345), "12,345")

    def test_idle_overlay_is_not_redrawn_and_changed_totals_are(self):
        now = time.monotonic()
        self.app.encounter.add(Hit(1, 99, 1, 100), now)
        self.app.overlay.metric.set("all")
        rows = self.app.rows("all", now)
        self.app.overlay.paint(rows, now)
        self.root.update()
        canvas = self.app.overlay.canvas
        with patch.object(canvas, "delete") as delete:
            self.app.overlay.paint(rows, now)
            delete.assert_not_called()
            self.app.encounter.add_received(Hit(99, 1, 2, 300), now)
            self.app.overlay.paint(self.app.rows("all", now), now)
            delete.assert_called_once_with("all")

    def test_reset_and_party_updates_preserve_identity(self):
        now = time.monotonic()
        self.app.encounter.add_received(Hit(99, 1, 2, 300), now)
        self.app.encounter.add_tank(TankEvent(1, 1, "absorbed", 400, 2), now)
        self.app.metric.set("received")
        self.app.tick()
        self.root.update()
        self.assertEqual(self.app.rows()[0][1], 700)
        self.app.overlay.reset_button.invoke()
        self.assertFalse(self.app.encounter.players)
        self.assertEqual(self.app.group, {1, 2})
        self.app.events.put(("party_roster", [(0, "Player", 1)]))
        self.app.events.put(("party", (2, "", 0)))
        self.app.tick()
        self.assertEqual(self.app.group, {1})
        self.assertEqual(self.app.names[1], "Player")

    def test_status_recovers_party_after_starting_without_roster(self):
        self.app.group = {1}
        self.app.events.put(("party", (2, "", 0)))
        self.app._drain_events()
        self.assertEqual(self.app.group, {1, 2})

    def test_status_received_before_own_identity_lists_party_immediately(self):
        self.app.me = None
        self.app.group = set()
        self.app.events.put(("party", (2, "", 0)))
        self.app._drain_events()
        self.assertEqual(self.app.group, {2})
        self.assertEqual([row[0] for row in self.app.rows()], [2])
        self.app.events.put(("name", (1, "Player", True)))
        self.app._drain_events()
        self.assertEqual(self.app.group, {1, 2})

    def test_reset_preserves_identity_and_party_packets_waiting_in_queue(self):
        self.app.group = set()
        self.app.me = None
        self.app.events.put(("name", (1, "Player", True)))
        self.app.events.put(("party", (2, "Healer", 2)))
        self.app.events.put(("hit", (Hit(1, 99, 1, 100), time.monotonic())))
        self.app.reset()
        self.assertEqual(self.app.me, 1)
        self.assertEqual(self.app.group, {1, 2})
        self.assertEqual(self.app.names[2], "Healer")
        self.assertFalse(self.app.encounter.players)
