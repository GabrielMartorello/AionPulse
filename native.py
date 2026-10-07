# SPDX-License-Identifier: GPL-3.0-only
import ctypes as C
import os
import struct
from pathlib import Path
from dataclasses import dataclass


class Address(C.Structure):
    pass


Address._fields_ = [
    ("next", C.POINTER(Address)),
    ("addr", C.c_void_p),
    ("mask", C.c_void_p),
    ("broadcast", C.c_void_p),
    ("destination", C.c_void_p),
]


class Device(C.Structure):
    pass


Device._fields_ = [
    ("next", C.POINTER(Device)),
    ("name", C.c_char_p),
    ("description", C.c_char_p),
    ("addresses", C.POINTER(Address)),
    ("flags", C.c_uint),
]


class Header(C.Structure):
    _fields_ = [
        ("seconds", C.c_long),
        ("micros", C.c_long),
        ("caplen", C.c_uint),
        ("length", C.c_uint),
    ]


class Bpf(C.Structure):
    _fields_ = [("length", C.c_uint), ("instructions", C.c_void_p)]


class Stats(C.Structure):
    _fields_ = [
        ("received", C.c_uint),
        ("dropped", C.c_uint),
        ("interface_dropped", C.c_uint),
        ("captured", C.c_uint),
    ]


@dataclass(frozen=True)
class Interface:
    name: str
    device: str
    ip: str


_dll = None
_directory = None


def library():
    global _dll, _directory
    if _dll is not None:
        return _dll
    path = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "Npcap"
    _directory = os.add_dll_directory(str(path))
    _dll = C.CDLL(str(path / "wpcap.dll"))
    declarations = {
        "pcap_findalldevs": ([C.POINTER(C.POINTER(Device)), C.c_char_p], C.c_int),
        "pcap_freealldevs": ([C.POINTER(Device)], None),
        "pcap_open_live": ([C.c_char_p, C.c_int, C.c_int, C.c_int, C.c_char_p], C.c_void_p),
        "pcap_compile": ([C.c_void_p, C.POINTER(Bpf), C.c_char_p, C.c_int, C.c_uint], C.c_int),
        "pcap_setfilter": ([C.c_void_p, C.POINTER(Bpf)], C.c_int),
        "pcap_freecode": ([C.POINTER(Bpf)], None),
        "pcap_next_ex": (
            [C.c_void_p, C.POINTER(C.POINTER(Header)), C.POINTER(C.POINTER(C.c_ubyte))],
            C.c_int,
        ),
        "pcap_setnonblock": ([C.c_void_p, C.c_int, C.c_char_p], C.c_int),
        "pcap_datalink": ([C.c_void_p], C.c_int),
        "pcap_geterr": ([C.c_void_p], C.c_char_p),
        "pcap_stats": ([C.c_void_p, C.POINTER(Stats)], C.c_int),
        "pcap_close": ([C.c_void_p], None),
    }
    for name, (args, result) in declarations.items():
        function = getattr(_dll, name)
        function.argtypes, function.restype = args, result
    return _dll


def interfaces():
    lib = library()
    head = C.POINTER(Device)()
    error = C.create_string_buffer(256)
    if lib.pcap_findalldevs(C.byref(head), error):
        raise RuntimeError(error.value.decode(errors="replace"))
    result = []
    try:
        current = head
        while current:
            item = current.contents
            description = (item.description or item.name).decode(errors="replace")
            addr = item.addresses
            addresses = []
            while addr:
                if addr.contents.addr:
                    raw = C.string_at(addr.contents.addr, 16)
                    if struct.unpack_from("<H", raw)[0] == 2:
                        addresses.append(".".join(str(v) for v in raw[4:8]))
                addr = addr.contents.next
            ip = addresses[0] if addresses else ""
            if addresses or "loopback" in description.lower():
                label = f"{description} · {ip}" if ip else description
                result.append((label, Interface(label, item.name.decode(), ip)))
            current = item.next
    finally:
        lib.pcap_freealldevs(head)
    return result


def tcp_payload(data, datalink):

    if datalink == 1:
        if len(data) < 14:
            return None
        ether_type = struct.unpack_from("!H", data, 12)[0]
        pos = 14
        for _ in range(2):
            if ether_type not in (0x8100, 0x88A8):
                break
            if len(data) < pos + 4:
                return None
            ether_type = struct.unpack_from("!H", data, pos + 2)[0]
            pos += 4
        if ether_type not in (0x0800, 0x86DD):
            return None
    elif datalink in (0, 108):
        pos = 4
    elif datalink in (12, 101):
        pos = 0
    else:
        raise ValueError(f"Tipo de interface não suportado: {datalink}")
    if len(data) <= pos:
        return None
    version = data[pos] >> 4
    if version == 4:
        if len(data) < pos + 20 or data[pos + 9] != 6:
            return None
        ihl = (data[pos] & 15) * 4
        total = struct.unpack_from("!H", data, pos + 2)[0]
        if ihl < 20 or total < ihl + 20 or len(data) < pos + total:
            return None
        if struct.unpack_from("!H", data, pos + 6)[0] & 0x3FFF:
            return None
        src, dst = data[pos + 12 : pos + 16], data[pos + 16 : pos + 20]
        end, pos = pos + total, pos + ihl
    elif version == 6:
        if len(data) < pos + 40 or data[pos + 6] != 6:
            return None
        length = struct.unpack_from("!H", data, pos + 4)[0]
        if length < 20 or len(data) < pos + 40 + length:
            return None
        src, dst = data[pos + 8 : pos + 24], data[pos + 24 : pos + 40]
        end, pos = pos + 40 + length, pos + 40
    else:
        return None
    sport, dport, seq = struct.unpack_from("!HHI", data, pos)
    header_size = (data[pos + 12] >> 4) * 4
    if header_size < 20 or pos + header_size > end:
        return None
    return (src, dst, sport, dport), seq, data[pos + 13], data[pos + header_size : end]


class Listener:
    def __init__(self, interface, port):
        self.lib = library()
        self.handle = None
        error = C.create_string_buffer(256)
        self.handle = self.lib.pcap_open_live(interface.device.encode(), 65535, 0, 250, error)
        if not self.handle:
            raise RuntimeError(error.value.decode(errors="replace"))
        try:
            if self.lib.pcap_setnonblock(self.handle, 1, error) < 0:
                raise RuntimeError(error.value.decode(errors="replace"))
            program = Bpf()
            if (
                self.lib.pcap_compile(
                    self.handle, C.byref(program), f"tcp src port {port}".encode(), 1, 0xFFFFFFFF
                )
                < 0
            ):
                raise RuntimeError(self.error())
            try:
                if self.lib.pcap_setfilter(self.handle, C.byref(program)) < 0:
                    raise RuntimeError(self.error())
            finally:
                self.lib.pcap_freecode(C.byref(program))
            self.datalink = self.lib.pcap_datalink(self.handle)
            if self.datalink not in (0, 1, 12, 101, 108):
                raise RuntimeError(f"Tipo de interface não suportado: {self.datalink}")
        except Exception:
            self.close()
            raise

    def error(self):
        return self.lib.pcap_geterr(self.handle).decode(errors="replace")

    def next(self):
        header, packet = C.POINTER(Header)(), C.POINTER(C.c_ubyte)()
        result = self.lib.pcap_next_ex(self.handle, C.byref(header), C.byref(packet))
        if result < 0:
            raise RuntimeError(self.error())
        if result == 0:
            return None
        return C.string_at(packet, header.contents.caplen)

    def drops(self):
        stats = Stats()
        return stats.dropped if self.lib.pcap_stats(self.handle, C.byref(stats)) == 0 else 0

    def close(self):
        if self.handle:
            self.lib.pcap_close(self.handle)
            self.handle = None
