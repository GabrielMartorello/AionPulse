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

    if data[:2] == b"\x02\x97":
        return named_party_roster(data)
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


def named_party_roster(data):
    if data[:2] != b"\x02\x97":
        return None
    try:
        pos = 6
        size = data[pos]
        pos += 1
        if not 1 <= size <= 40:
            return None
        label = data[pos : pos + size].decode("utf-8")
        if len(data[pos : pos + size]) != size or not label.strip() or not label.isprintable():
            return None
        pos += size
        capacity = data[pos]
        pos += 18
        count, pos = varint(data, pos)
        if not 1 <= count <= capacity <= 12:
            return None
        rows = []
        for index in range(count):
            if pos + 11 > len(data):
                return None
            slot = data[pos + 1]
            server = int.from_bytes(data[pos + 8 : pos + 10], "little")
            size = data[pos + 10]
            if not 1 <= slot <= capacity:
                return None
            if size == 0:
                if data[pos] != 0:
                    return None
                break
            if not 1 <= server <= 9999 or not 1 <= size <= 40 or pos + 11 + size + 12 > len(data):
                return None
            name = data[pos + 11 : pos + 11 + size].decode("utf-8")
            if (
                not 1 <= len(name) <= 12
                or not all(c.isalnum() for c in name)
                or not any(c.isalpha() for c in name)
            ):
                return None
            pos += 11 + size
            _, level, gear = struct.unpack_from("<III", data, pos)
            if not 1 <= level <= 200 or gear > 1_000_000:
                return None
            pos += 12
            anchors = [
                candidate
                for candidate in range(pos, min(pos + 11, len(data) - 12))
                if int.from_bytes(data[candidate : candidate + 2], "little") == server
                and int.from_bytes(data[candidate + 5 : candidate + 13], "little") <= 100_000_000
            ]
            if len(anchors) != 1:
                return None
            pos = anchors[0] + 13
            rows.append((0, name, slot))
            if index + 1 == count:
                break
            candidates = [
                candidate
                for candidate in range(pos, min(pos + 33, len(data) - 10))
                if data[candidate + 1] == slot + 1
                and (
                    1 <= int.from_bytes(data[candidate + 8 : candidate + 10], "little") <= 9999
                    or (data[candidate] == 0 and data[candidate + 10] == 0)
                )
                and data[candidate + 10] <= 40
                and candidate + 11 + data[candidate + 10] <= len(data)
            ]
            if len(candidates) != 1:
                return None
            pos = candidates[0]
        if len({row[1] for row in rows}) != len(rows) or len({row[2] for row in rows}) != len(rows):
            return None
        return rows or None
    except (ValueError, IndexError, UnicodeError, struct.error):
        return None


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

