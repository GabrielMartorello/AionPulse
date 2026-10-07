# SPDX-License-Identifier: GPL-3.0-only
import math
import struct


def character_identity(data):
    if data[:2] != b"\x45\x36":
        return None
    marker = b"\x0e\x01\x01"
    candidates = set()
    offset = data.find(marker)
    while offset >= 0:
        start = offset + len(marker)
        if start + 9 <= len(data):
            character = int.from_bytes(data[start : start + 4], "little")
            server = int.from_bytes(data[start + 6 : start + 8], "little")
            if (
                character > 0
                and data[start + 4 : start + 6] == bytes(2)
                and 1001 <= server <= 2999
                and data[start + 8] == 4
            ):
                candidates.add((character, server))
        offset = data.find(marker, offset + 1)
    return next(iter(candidates)) if len(candidates) == 1 else None


def remote_party_identity(data):
    if data[:2] != b"\x1c\x92" or len(data) != 65:
        return None
    body = data[2:]
    character = int.from_bytes(body[:4], "little")
    server = int.from_bytes(body[6:8], "little")
    level = int.from_bytes(body[8:12], "little")
    if (
        character <= 0
        or body[4:6] != bytes(2)
        or not 1001 <= server <= 2999
        or not 1 <= level <= 100
        or body[-1] > 1
    ):
        return None
    if not all(
        math.isfinite(value) and abs(value) < 1e9 for value in struct.unpack_from("<fff", body, 24)
    ):
        return None
    return character, server


class PartyIdentity:
    def __init__(self):
        self.clear()

    def clear(self):
        self.identities = {}
        self.remote = set()
        self.emitted = {}

    def observe(self, data, name=None):
        remote = remote_party_identity(data)
        if remote and len(self.remote) < 6:
            self.remote.add(remote)
        if name:
            identity = character_identity(data)
            if identity:
                if identity not in self.identities and len(self.identities) >= 512:
                    self.identities.pop(next(iter(self.identities)))
                self.identities[identity] = name[:2]
        members = []
        for identity in self.remote:
            player = self.identities.get(identity)
            if player and self.emitted.get(identity) != player:
                self.emitted[identity] = player
                members.append((*player, 0))
        return members
