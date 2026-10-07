# SPDX-License-Identifier: GPL-3.0-only
import struct
from dataclasses import dataclass
from protocol import varint


@dataclass(frozen=True)
class TankEvent:
    target: int
    skill: int
    metric: str
    amount: int
    actor: int = 0
    defenses: tuple = ()


class TankParser:
    def __init__(self):
        self.pools = {}

    def clear(self):
        self.pools.clear()

    def parse(self, data):
        try:
            target, pos = varint(data, 2)
            layout, pos = varint(data, pos)
            if data[:2] == b"\x05\x38":
                actor, pos = varint(data, pos)
                chain, pos = varint(data, pos)
                body = struct.unpack_from("<I", data, pos)[0]
                remaining, pos = varint(data, pos + 4)
                tail = data[pos:]

                skill, emitted = 0, 0
                if len(tail) == 4:
                    skill = struct.unpack("<I", tail)[0]
                elif len(tail) > 4:
                    emitted, end = varint(tail[:-4], 0)
                    if end != len(tail) - 4:
                        return [], False
                    skill = struct.unpack("<I", tail[-4:])[0]
                elif tail:
                    emitted, end = varint(tail, 0)
                    if end != len(tail):
                        return [], False
                if not target or not actor or not chain or remaining > 99_999_999:
                    return [], False
                key = (target, chain, skill or body)
                if layout == 9 and remaining > 0:
                    if len(self.pools) >= 4096:
                        self.pools.pop(next(iter(self.pools)))
                    self.pools[key] = (actor, remaining, False)
                    return [], True
                if layout == 10 and key in self.pools:
                    del self.pools[key]
                    return [], True
                if layout == 11 and key in self.pools:
                    caster, grant, confirmed = self.pools[key]
                    if actor == caster:
                        return [], False
                    self.pools[key] = (caster, grant, True)
                    if not 0 < emitted <= 99_999_999:
                        return [], True
                    events = [TankEvent(target, skill or body, "absorbed", emitted, caster)]
                    if not confirmed:
                        events.append(
                            TankEvent(target, skill or body, "shield_granted", grant, caster)
                        )
                    return events, True
                return [], False
            if data[:2] != b"\x04\x38":
                return [], False
            flag, pos = varint(data, pos)
            actor, pos = varint(data, pos)
            skill = struct.unpack_from("<I", data, pos)[0]
            _, pos = varint(data, pos + 5)
            if actor == target or not actor or not target or layout > 255:
                return [], False
            if layout & 15 != 6 or not layout & 0x40 or flag != 0x10 or pos + 10 > len(data):
                return [], False
            action = data[pos]

            for _ in range(3):
                _, pos = varint(data, pos + 10 if _ == 0 else pos)
            kinds = tuple(name for bit, name in ((1, "block"), (2, "parry")) if action & bit)
            return ([TankEvent(target, skill, "defenses", 1, actor, kinds)] if kinds else []), False
        except (ValueError, IndexError, struct.error):
            return [], False
