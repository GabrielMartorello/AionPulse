# SPDX-License-Identifier: GPL-3.0-only
from collections import defaultdict, deque


class Encounter:
    CURRENT_WINDOW = 5.0

    def __init__(self):
        self.clear()

    def clear(self):
        self.first = None
        self.last = None
        self.recent = deque()
        self.support_recent = deque()
        self.rate_totals = defaultdict(lambda: defaultdict(int))
        self.players = defaultdict(
            lambda: {
                "damage": 0,
                "hits": 0,
                "crit": 0,
                "skills": defaultdict(int),
                "first": None,
                "last": None,
                "received": 0,
                "health_received": 0,
                "mitigated": 0,
                "healing": 0,
                "recovery": 0,
                "potion": 0,
                "absorbed": 0,
                "defenses": 0,
                "shield_granted": 0,
                "block": 0,
                "parry": 0,
                "support_hits": defaultdict(int),
                "support_skills": defaultdict(lambda: defaultdict(int)),
            }
        )

    def _touch(self, actor, now):
        if self.first is None:
            self.first = now
        self.last = now
        player = self.players[actor]
        if player["first"] is None:
            player["first"] = now
        player["last"] = now
        return player

    def _support(self, actor, metric, amount, skill, now):
        player = self._touch(actor, now)
        player[metric] += amount
        player["support_hits"][metric] += 1
        player["support_skills"][metric][skill] += amount
        self.support_recent.append((now, actor, metric, amount))
        self.rate_totals[metric][actor] += amount
        self._prune_recent(now)

    def add_received(self, hit, now):
        self.players[hit.target]["health_received"] += hit.damage
        self._support(hit.target, "received", hit.damage, hit.skill, now)

    def add_tank(self, event, now):
        self._support(event.target, event.metric, event.amount, event.skill, now)

        if event.metric in ("absorbed", "mitigated"):
            self._support(event.target, "received", event.amount, event.skill, now)
        for kind in event.defenses:
            self.players[event.target][kind] += 1

    def add_heal(self, heal, now):
        self._support(heal.target, "recovery", heal.amount, heal.skill, now)
        if heal.category == "skill":
            self._support(heal.actor, "healing", heal.amount, heal.skill, now)
        elif heal.category == "potion":
            self.players[heal.target]["potion"] += heal.amount

    def add(self, hit, now):
        self.recent.append((now, hit.actor, hit.damage))
        self.rate_totals["damage"][hit.actor] += hit.damage
        self._prune_recent(now)
        player = self._touch(hit.actor, now)
        player["damage"] += hit.damage
        player["hits"] += 1
        player["crit"] += int(hit.critical)
        player["skills"][hit.skill] += hit.damage

    def _prune_recent(self, now):
        while self.recent and self.recent[0][0] <= now - self.CURRENT_WINDOW:
            _, actor, amount = self.recent.popleft()
            self._subtract_rate("damage", actor, amount)
        while self.support_recent and self.support_recent[0][0] <= now - self.CURRENT_WINDOW:
            _, actor, metric, amount = self.support_recent.popleft()
            self._subtract_rate(metric, actor, amount)

    def _subtract_rate(self, metric, actor, amount):
        totals = self.rate_totals[metric]
        totals[actor] -= amount
        if not totals[actor]:
            del totals[actor]

    def current_dps(self, now):
        return self.current_rate(now, "damage")

    def current_rate(self, now, metric="damage"):
        self._prune_recent(now)
        if self.last is None or self.last <= now:
            return {
                actor: amount / self.CURRENT_WINDOW
                for actor, amount in self.rate_totals.get(metric, {}).items()
            }
        totals = defaultdict(int)
        events = (
            ((stamp, actor, "damage", amount) for stamp, actor, amount in self.recent)
            if metric == "damage"
            else self.support_recent
        )
        for timestamp, actor, kind, amount in events:
            if kind == metric and timestamp <= now:
                totals[actor] += amount
        return {actor: amount / self.CURRENT_WINDOW for actor, amount in totals.items()}

    def duration(self, now, group=None):
        first, last = self.first, self.last
        if group is not None:
            players = [
                p for actor, p in self.players.items() if actor in group and p["first"] is not None
            ]
            if not players:
                return 0
            first = min(p["first"] for p in players)
            last = max(p["last"] for p in players)
        if first is None:
            return 0
        end = now if now - last < 10 else last
        return max(1.0, end - first)

    def rows(self, now, group=None, metric="damage"):
        seconds = self.duration(now, group)
        rows = [
            (
                actor,
                p[metric],
                p[metric] / max(1, seconds),
                p["hits"] if metric == "damage" else p["support_hits"][metric],
                p["crit"] if metric == "damage" else 0,
                dict(p["skills"] if metric == "damage" else p["support_skills"][metric]),
            )
            for actor, p in self.players.items()
            if p["first"] is not None and (group is None or actor in group)
        ]
        return sorted(rows, key=lambda row: row[1], reverse=True)
