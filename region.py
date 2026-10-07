# SPDX-License-Identifier: GPL-3.0-only
from ipaddress import ip_address

OBSERVED_SERVERS = {
    "193.202.112.174": "América do Sul",
    "193.202.112.191": "América do Sul",
}


def detect_region(address):
    try:
        address = ip_address(address)
    except ValueError:
        return "não identificada"
    if str(address) in OBSERVED_SERVERS:
        return OBSERVED_SERVERS[str(address)]
    if address.version == 4 and address.packed[:3] == bytes((206, 127, 156)):
        return "Coreia"
    return "não identificada"
