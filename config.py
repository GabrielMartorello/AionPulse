# SPDX-License-Identifier: GPL-3.0-only
import json
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
DATA_ROOT = Path(
    os.environ.get("AIONPULSE_DATA_DIR")
    or Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "AionPulse"
)


class Preferences:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else DATA_ROOT / "preferences.json"
        try:
            self.values = json.loads(self.path.read_text(encoding="utf-8-sig"))
            if not isinstance(self.values, dict):
                self.values = {}
        except (OSError, ValueError):
            self.values = {}

    def update(self, **changes):
        if all(self.values.get(key) == value for key, value in changes.items()):
            return
        self.values.update(changes)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self.values, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
