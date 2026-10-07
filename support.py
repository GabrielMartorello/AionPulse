# SPDX-License-Identifier: GPL-3.0-only
import struct
from dataclasses import dataclass
from protocol import varint, Hit


HEALING_SKILLS = {
    17090000,
    17100000,
    17120000,
    17270000,
    17290000,
    17320000,
    17800000,
    18120000,
    18170000,
}

POTION_SKILLS = {2010101}

SELF_HEALING_VARIANTS = {12720001, 12350000}


@dataclass(frozen=True)
class Heal:
    actor: int
    target: int
    skill: int
    amount: int
    category: str = "skill"


def is_healing_skill(skill):
    return skill // 10000 * 10000 in HEALING_SKILLS


def support_events(data):

    try:
        target, pos = varint(data, 2)
        layout, pos = varint(data, pos)
        if data[:2] == b"\x05\x38":
            actor, pos = varint(data, pos)
            _, pos = varint(data, pos)
            skill = struct.unpack_from("<I", data, pos)[0]
            amount, pos = varint(data, pos + 4)
            if not actor or not target or not 0 < amount <= 99_999_999:
                return [], []
            if actor == target and layout == 11:
                return [], [Heal(actor, target, skill, amount, "recovery")]
            if layout in (1, 2, 3) and is_healing_skill(skill):
                return [], [Heal(actor, target, skill, amount)]
            if actor != target and layout in (2, 3):
                return [Hit(actor, target, skill, amount, dot=True)], []
            return [], []
        if data[:2] != b"\x04\x38":
            return [], []
        flag, pos = varint(data, pos)
        actor, pos = varint(data, pos)
        if not actor or not target or layout > 255 or flag > 255:
            return [], []
        skill = struct.unpack_from("<I", data, pos)[0]
        dtype, pos = varint(data, pos + 5)
        key = layout & 15
        size = {4: 8, 5: 12, 6: 10, 7: 14}.get(key)
        if size is None or pos + size > len(data) or dtype > 255:
            return [], []
        detail = data[pos : pos + size]
        unknown, pos = varint(data, pos + size)
        amount, pos = varint(data, pos)
        loop, pos = varint(data, pos)

        if key == 6 and unknown == 0 and loop > 0:
            amount = loop
            if detail[0] & 0x20 and amount > 0:
                try:
                    extra, _ = varint(data, pos)
                    if extra > 0:
                        amount = extra
                except ValueError:
                    pass
        heals = []
        if key == 6 and detail[0] & 0x20:
            regeneration, _ = varint(detail, 1)
            if 0 < regeneration <= 99_999_999:
                heals.append(Heal(target, target, 0, regeneration, "regeneration"))
        if not 0 < amount <= 99_999_999:
            return [], heals
        if size == 8 and detail[0] == 0x58:
            return [], heals
        if skill in POTION_SKILLS and actor == target and key == 4:
            return [], heals + [Heal(actor, target, skill, amount, "potion")]
        if actor == target and skill in SELF_HEALING_VARIANTS:
            return [], heals + [Heal(actor, target, skill, amount)]
        if (size == 8 and detail[0] == 0x57) or is_healing_skill(skill):
            return [], heals + [Heal(actor, target, skill, amount)]
        if actor == target:
            return [], heals
        return [Hit(actor, target, skill, amount, dtype == 3)], heals
    except (ValueError, IndexError, struct.error):
        return [], []
