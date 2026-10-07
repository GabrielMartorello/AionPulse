# SPDX-License-Identifier: GPL-3.0-only
import struct
import uuid
from protocol import varint


def _row(body, offset, listed=False, allow_profile=False):
    shift = 1 if listed else 0
    if len(body) - offset < 56 + shift:
        return None
    row = body[offset:]
    if listed:
        if row[0] > 5 or row[1] > 7 or not 1 <= row[2] <= 6:
            return None
    elif row[0] not in ((0, 3) if allow_profile else (3,)) or not 1 <= row[1] <= (
        6 if allow_profile else 5
    ):
        return None
    actor = struct.unpack_from("<i", row, 2 + shift)[0]
    server = struct.unpack_from("<H", row, 6 + shift)[0]
    if actor < 0 or (actor == 0 and not allow_profile) or not server or row[10 + shift] != 36:
        return None
    try:
        uuid.UUID(row[11 + shift : 47 + shift].decode("ascii"))
        if struct.unpack_from("<H", row, 53 + shift)[0] != server:
            return None
        length = row[55 + shift]
        raw = row[56 + shift : 56 + shift + length]
        if not length or len(raw) != length:
            return None
        name = raw.decode("utf-8")
        if not name.strip() or any(not c.isprintable() for c in name):
            return None
        return actor, name, row[1 + shift]
    except (ValueError, UnicodeError, struct.error):
        return None


def party_members(data):

    body = data[2:]
    if data[:2] == b"\x0d\x92":
        member = _row(body, 0, allow_profile=True)
        return [member] if member and member[0] > 0 else []
    if data[:2] == b"\x00\x92":
        members = []
        offset = 34 if len(body) > 34 and body[0] == 1 else 25
        while offset <= len(body) - 57 and len(members) < 6:
            member = _row(body, offset, listed=True)
            if member:
                members.append(member)
                offset += max(112, 57 + len(member[1].encode("utf-8")) + 32)
            else:
                offset += 1
        return members
    if data[:2] == b"\x1b\x92":
        try:
            actor, pos = varint(body)
            current, pos = varint(body, pos)
            maximum, pos = varint(body, pos)
            if (
                0 < actor <= 0x7FFFFFFF
                and 0 < maximum
                and current <= maximum
                and len(body) - pos == 25
                and body[-1] <= 1
            ):
                return [(actor, "", 0)]
        except ValueError:
            pass
    return []


def party_snapshot(data):

    if data[:2] != b"\x00\x92":
        return None
    body = data[2:]
    markers = []
    for pos in range(len(body) - 36):
        if body[pos] == 36:
            try:
                uuid.UUID(body[pos + 1 : pos + 37].decode("ascii"))
                markers.append(pos)
            except (ValueError, UnicodeError):
                pass
    if not 1 <= len(markers) <= 6:
        return None
    result = []
    for marker in markers:
        offset = marker - 11
        if offset < 25:
            return None
        member = _row(body, offset, listed=True)
        if not member or offset + 146 + len(member[1].encode("utf-8")) > len(body):
            return None
        result.append(member)
    if len({m[0] for m in result}) != len(result) or len({m[2] for m in result}) != len(result):
        return None
    return result


def party_roster(data):

    if data[:2] != b"\x00\x92":
        return None
    body = data[2:]
    markers = []
    for pos in range(len(body) - 36):
        if body[pos] == 36:
            try:
                uuid.UUID(body[pos + 1 : pos + 37].decode("ascii"))
                markers.append(pos)
            except (ValueError, UnicodeError):
                pass
    if not 1 <= len(markers) <= 6:
        return None
    rows = []
    for marker in markers:
        found = []
        for listed, prefix in ((True, 11), (False, 10)):
            offset = marker - prefix
            if offset < 25:
                continue
            member = _row(body, offset, listed=listed, allow_profile=True)
            if member and offset + 146 + len(member[1].encode("utf-8")) <= len(body):
                found.append(member)
        if not found or len(set(found)) != 1:
            return None
        rows.append(found[0])
    if len({row[2] for row in rows}) != len(rows):
        return None
    return rows


def resolve_party_roster(roster, names, me):

    if roster is None or me is None:
        return None
    resolved = []
    for actor, name, slot in roster:
        if actor == 0:
            candidates = [entity for entity, known in names.items() if known == name]
            if len(candidates) != 1:
                return None
            actor = candidates[0]
        resolved.append((actor, name, slot))
    members = {row[0] for row in resolved}
    if me not in members or len(members) != len(resolved):
        return None
    return resolved
