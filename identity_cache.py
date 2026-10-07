# SPDX-License-Identifier: GPL-3.0-only
import hashlib
import json
import time
from pathlib import Path


def connection_key(key):
    source, destination, sport, dport = key
    value = f"{source.hex()}/{destination.hex()}/{sport}/{dport}"
    return hashlib.sha256(value.encode("ascii")).hexdigest()


class IdentityCache:
    TTL = 900

    def __init__(self, path):
        self.path = Path(path)
        self.roster_confirmed = False

    def restore(self, key, now=None):
        self.roster_confirmed = False
        now = time.time() if now is None else now
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
            if data["connection"] != key or not 0 <= now - data["updated"] < self.TTL:
                return {}, None, set()
            names = {
                int(actor): name
                for actor, name in data["names"].items()
                if int(actor) > 0 and isinstance(name, str) and 0 < len(name) <= 71
            }
            actor = int(data.get("self_id") or 0)
            me = actor if actor in names else None
            group = {int(actor) for actor in data.get("observed_group", []) if int(actor) > 0}
            self.roster_confirmed = bool(data.get("roster_confirmed", False))
            return names, me, group
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return {}, None, set()

    def load(self, key, now=None):
        return self.restore(key, now)[0]

    def load_self(self, key, now=None):
        return self.restore(key, now)[1]

    def load_group(self, key, now=None):
        return self.restore(key, now)[2]

    def save(self, key, names, now=None, self_id=None, group=(), roster_confirmed=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "connection": key,
            "updated": time.time() if now is None else now,
            "names": dict(list(names.items())[-512:]),
            "self_id": self_id if self_id in names else None,
            "observed_group": sorted(group),
            "roster_confirmed": roster_confirmed,
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)
