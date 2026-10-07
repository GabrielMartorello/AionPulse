# SPDX-License-Identifier: GPL-3.0-only
import struct
import unicodedata
from collections import Counter
from dataclasses import dataclass


def varint(data, offset=0):
    value = 0
    for index in range(5):
        if offset + index >= len(data):
            raise ValueError("Varint incompleto")
        byte = data[offset + index]
        if index == 4 and byte > 15:
            raise ValueError("Varint fora de uint32")
        value |= (byte & 127) << (index * 7)
        if not byte & 128:
            return value, offset + index + 1
    raise ValueError("Varint inválido")


@dataclass(frozen=True)
class Hit:
    actor: int
    target: int
    skill: int
    damage: int
    critical: bool = False
    dot: bool = False


def damage_events(data):

    events = []
    try:
        if data[:2] == b"\x05\x38":
            target, pos = varint(data, 2)
            if not data[pos] & 2:
                return []
            actor, pos = varint(data, pos + 1)
            _, pos = varint(data, pos)
            skill = struct.unpack_from("<I", data, pos)[0]
            damage, pos = varint(data, pos + 4)
            if actor and 0 < damage <= 99_999_999:
                events.append(Hit(actor, target, skill, damage, dot=True))
            return events
        if data[:2] != b"\x04\x38":
            return []
        pos = 2
        while pos < len(data):
            if data[pos : pos + 2] == b"\x01\x00":
                pos += 2
            elif events:
                break
            target, pos = varint(data, pos)
            mode, pos = varint(data, pos)
            mode &= 15
            if mode not in (4, 5, 6, 7):
                break
            _, pos = varint(data, pos)
            actor, pos = varint(data, pos)
            if not actor:
                break
            skill = struct.unpack_from("<I", data, pos)[0]
            pos += 5
            if 3_000_000 <= skill <= 3_099_999:
                skill = skill * 10 + 1
            if not 1 <= skill <= 299_999_999 or 1_000_000 <= skill <= 9_999_999:
                break
            damage_type, pos = varint(data, pos)
            pos += {4: 8, 5: 12, 6: 10, 7: 14}[mode]
            unknown, pos = varint(data, pos)
            damage, pos = varint(data, pos)
            if unknown == 0:
                shifted, next_pos = varint(data, pos)
                try:
                    count, _ = varint(data, next_pos)
                except ValueError:
                    count = 0
                if shifted > 0 and 1 <= count <= 25:
                    damage, pos = shifted, next_pos

            try:
                count, cursor = varint(data, pos)
                values = []
                if 1 <= count <= 25:
                    for _ in range(count):
                        value, cursor = varint(data, cursor)
                        values.append(value)
                    if values and values[0] > 0 and len(set(values)) == 1:
                        pos = cursor
            except ValueError:
                pass
            if damage > 99_999_999:
                break
            if damage:
                events.append(Hit(actor, target, skill, damage, (damage_type & 255) == 3))
    except (ValueError, IndexError, struct.error):
        pass
    return events


def _legacy_nickname(data):

    if data[:2] not in (b"\x33\x36", b"\x45\x36", b"\x04\x8d"):
        return None
    try:
        actor, pos = varint(data, 2)
        if not actor:
            return None
        candidates = []
        if data[:2] == b"\x04\x8d":
            entity = actor
            actor, pos = varint(data, pos + 4)
            if not actor or actor == entity or pos + 3 > len(data):
                return None
            size, start = varint(data, pos + 2)
            candidates.append((start, size))
        elif data[:2] == b"\x33\x36":
            candidates.append((pos + 6, data[pos + 5]))
        else:
            _, pos = varint(data, pos)
            _, pos = varint(data, pos)
            for offset in range(pos + 1, pos + 6):
                try:
                    size, start = varint(data, offset)
                    candidates.append((start, size))
                except ValueError:
                    pass
        valid = []
        for start, size in candidates:
            if not 1 <= size <= 71 or start + size + 2 > len(data):
                continue
            try:
                name = data[start : start + size].decode("utf-8").split("\0", 1)[0].strip()
            except UnicodeDecodeError:
                continue
            if (
                len(name) >= 2
                and all(
                    c.isalnum() or c in "_-" or unicodedata.category(c).startswith("M")
                    for c in name
                )
                and not name.isdigit()
            ):
                valid.append(name)
        if valid:
            return actor, max(valid, key=len), data[:2] == b"\x33\x36"
    except (ValueError, IndexError):
        pass
    return None


def identity_records(data):
    records = []
    offset = 0
    while offset + 8 < len(data) and len(records) < 128:
        opcode = data[offset : offset + 2]
        if opcode not in (b"\x33\x36", b"\x44\x36", b"\x45\x36"):
            offset += 1
            continue
        try:
            actor, pos = varint(data, offset + 2)
            gate = pos + 4
            size = data[gate + 1]
            end = gate + 2 + size
            if not 0 < actor <= 9_999_999 or not data[gate] & 1 or not 1 <= size <= 48:
                offset += 1
                continue
            name = data[gate + 2 : end].decode("utf-8")
            if (
                end > len(data)
                or not 1 <= len(name) <= 12
                or not all(c.isalnum() for c in name)
                or not any(c.isalpha() for c in name)
            ):
                offset += 1
                continue
            records.append(((actor, name, opcode == b"\x33\x36"), data[offset:]))
            offset = end
        except (ValueError, IndexError, UnicodeError):
            offset += 1
    legacy = _legacy_nickname(data)
    if legacy and not any(record[0][0] == legacy[0] for record in records):
        records.insert(0, (legacy, data))
    by_actor = {}
    for player, _ in records:
        by_actor.setdefault(player[0], set()).add(player[1])
    self_ids = {player[0] for player, _ in records if player[2]}
    seen = set()
    valid = []
    for player, payload in records:
        if len(by_actor[player[0]]) != 1 or (player[2] and len(self_ids) != 1):
            continue
        if player not in seen:
            seen.add(player)
            valid.append((player, payload))
    return valid


def nickname(data):
    records = identity_records(data)
    return records[0][0] if records else None


class Framer:
    def __init__(self, callback):
        self.buffer = bytearray()
        self.callback = callback
        self.opcodes = Counter()
        self.skipped = 0
        self.errors = 0

    def feed(self, chunk, depth=0, inner=False):
        if depth > 3:
            self.errors += 1
            return
        self.buffer.extend(chunk)
        pos = 0
        while pos < len(self.buffer):
            if self.buffer[pos] == 0:
                pos += 1
                continue
            try:
                length, start = varint(self.buffer, pos)
            except ValueError:
                if len(self.buffer) - pos < 5:
                    break
                pos += 1
                self.skipped += 1
                continue
            total = length - 3
            if total < start - pos + 2 or total > 65535:
                pos += 1
                self.skipped += 1
                continue
            if start >= len(self.buffer):
                break
            if 0xF0 <= self.buffer[start] < 0xFF:
                start += 1
            opcode = bytes(self.buffer[start : start + 2])
            bundle = opcode == b"\xff\xff"
            end = pos + total + (1 if bundle and not inner else 0)
            if end > len(self.buffer):
                if total > 8192:
                    pos += 1
                    self.skipped += 1
                    continue
                break
            payload = bytes(self.buffer[start:end])
            self.opcodes[opcode.hex()] += 1
            if bundle:
                try:
                    import lz4.block

                    size = struct.unpack_from("<I", payload, 2)[0]
                    if not 0 < size <= 5_000_000:
                        raise ValueError("Bundle excede limite")
                    decoded = lz4.block.decompress(payload[6:], uncompressed_size=size)
                    child = Framer(self.callback)
                    child.feed(decoded, depth + 1, inner=True)
                    self.opcodes.update(child.opcodes)
                    self.errors += child.errors
                    self.skipped += child.skipped
                except (ValueError, struct.error, RuntimeError, lz4.block.LZ4BlockError):
                    self.errors += 1
            else:
                self.callback(payload)
            pos = end
        del self.buffer[:pos]
        if len(self.buffer) > 1_000_000:
            self.buffer.clear()
            self.errors += 1


class TcpStream:
    def __init__(self, callback):
        self.next_seq = None
        self.pending = {}
        self.framer = Framer(callback)
        self.resets = 0

    def feed(self, seq, payload):
        if not payload:
            return
        if self.next_seq is None:
            self.next_seq = seq
        seq = self.next_seq + ((seq - self.next_seq + 2**31) % 2**32 - 2**31)
        end = seq + len(payload)
        if end <= self.next_seq:
            return
        if seq > self.next_seq:
            self.pending.setdefault(seq, payload)
            if sum(map(len, self.pending.values())) > 1_000_000:
                self.pending.clear()
                self.framer.buffer.clear()
                self.next_seq = None
                self.resets += 1
            return
        self.framer.feed(payload[self.next_seq - seq :])
        self.next_seq = end
        for pending_seq in sorted(list(self.pending)):
            if pending_seq > self.next_seq:
                break
            self.feed(pending_seq % 2**32, self.pending.pop(pending_seq))
