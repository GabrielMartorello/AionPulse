# SPDX-License-Identifier: GPL-3.0-only
import json
import time
import tkinter as tk
from pathlib import Path
import lz4.block
from app import App
from capture import Capture
from protocol import Hit


def run(report):
    result = {"passed": False}
    root = None
    try:
        sample = b"AionPulse" * 100
        assert lz4.block.decompress(lz4.block.compress(sample)) == sample
        Capture.interfaces = staticmethod(lambda: [])
        root = tk.Tk()
        root.withdraw()
        app = App(root)
        app.me = 1
        app.names = {1: "Player", 2: "Healer"}
        app.group = {1, 2}
        app.encounter.add(Hit(1, 99, 1, 12345), time.monotonic())
        app.toggle_overlay()
        app.metric.set("all")
        app.tick()
        root.update_idletasks()
        assert len(app.table.get_children()) == 2
        assert app.overlay.exists()
        app.language.set("English")
        app.change_language()
        assert app.overlay.reset_button.cget("text") == "Reset"
        app.full_values.set(True)
        assert app.display_number(12345) == "12,345"
        app.overlay.reset_button.invoke()
        assert not app.encounter.players
        result = {
            "passed": True,
            "checks": [
                "bundled Python",
                "Tcl/Tk",
                "icons",
                "lz4",
                "party rows",
                "overlay",
                "language",
                "full values",
                "reset",
            ],
        }
        app.quit()
        root = None
    except Exception as error:
        result["error"] = str(error)
    finally:
        if root is not None:
            root.destroy()
        Path(report).write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not result["passed"]:
        raise SystemExit(1)
