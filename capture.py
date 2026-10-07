# SPDX-License-Identifier: GPL-3.0-only
import queue
import threading
import time
from region import detect_region
from i18n import tr
from protocol import TcpStream, damage_events, identity_records
from party import party_members, party_roster
from party_identity import PartyIdentity
from identity_cache import connection_key
from support import support_events, is_healing_skill
from tank import TankParser


class Capture:
    def __init__(self, events):
        self.events = events
        self.stop_event = threading.Event()
        self.thread = None
        self.packet_count = 0
        self.payload_bytes = 0
        self.dropped = 0
        self.streams = {}
        self.event_count = 0
        self.frame_count = 0
        self.parse_errors = 0
        self.sync_skipped = 0
        self.kernel_dropped = 0
        self.heal_count = 0
        self.incoming_count = 0
        self.listener_restarts = 0
        self.tank_parser = TankParser()
        self.party_identity = PartyIdentity()

    @staticmethod
    def interfaces():
        from native import interfaces

        return interfaces()

    def publish(self, kind, data):
        try:
            self.events.put_nowait((kind, data))
        except queue.Full:
            self.dropped += 1

    def start(self, interface, port):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.streams.clear()
        self.tank_parser.clear()
        self.party_identity.clear()
        self.thread = threading.Thread(target=self.run, args=(interface, port), daemon=True)
        self.thread.start()

    def run(self, interface, port):
        try:
            from native import Listener, tcp_payload

            self.publish("status", f"{tr('Capturando em ')}{interface.name}{tr(' · porta ')}{port}")

            def callback(packet):
                if self.stop_event.is_set():
                    return
                decoded = tcp_payload(packet, listener.datalink)
                if not decoded:
                    return
                key, seq, flags, payload = decoded
                if key[2] != port:
                    return
                if flags & 2:
                    self.streams.pop(key, None)
                if not payload:
                    return
                self.packet_count += 1
                self.payload_bytes += len(payload)
                if key not in self.streams:
                    self.tank_parser.clear()
                    self.party_identity.clear()
                    if len(self.streams) >= 16:
                        self.streams.pop(next(iter(self.streams)))
                    self.streams[key] = TcpStream(self.parse)
                    self.publish("connection", (connection_key(key), bool(flags & 2)))
                    self.publish("region", detect_region(key[0]))
                self.streams[key].feed(seq, payload)
                if flags & 5:
                    self.streams.pop(key, None)

            listener = Listener(interface, port)
            last_packet = time.monotonic()
            last_stats = 0
            try:
                while not self.stop_event.is_set():
                    packet = listener.next()
                    if packet:
                        last_packet = time.monotonic()
                        callback(packet)
                        if last_packet - last_stats >= 1:
                            self.kernel_dropped = listener.drops()
                            last_stats = last_packet
                    elif time.monotonic() - last_packet > 30:
                        listener.close()
                        listener = Listener(interface, port)
                        self.listener_restarts += 1
                        last_packet = time.monotonic()
                    else:
                        self.stop_event.wait(0.01)
            finally:
                listener.close()
        except Exception as error:
            self.publish("status", f"{tr('Falha na captura: ')}{error}")
            self.publish("error", str(error))
        finally:
            self.stop_event.set()

    def parse(self, payload):
        self.frame_count += 1
        for member in party_members(payload):
            self.publish("party", member)
        roster = party_roster(payload)
        if roster is not None:
            self.publish("party_roster", roster)
        for name, identity_payload in identity_records(payload):
            self.publish("name", name)
            for member in self.party_identity.observe(identity_payload, name):
                self.publish("party", member)
        for member in self.party_identity.observe(payload):
            self.publish("party", member)
        if payload[:2] not in (b"\x04\x38", b"\x05\x38"):
            return
        now = time.monotonic()
        tank_events, tank_only = self.tank_parser.parse(payload)
        for event in tank_events:
            self.publish("tank", (event, now))
        if tank_only:
            return
        incoming, heals = support_events(payload)
        for hit in incoming:
            self.incoming_count += 1
            self.publish("incoming", (hit, now))
        for heal in heals:
            self.heal_count += 1
            self.publish("heal", (heal, now))
        healing_pairs = {(heal.actor, heal.target, heal.skill) for heal in heals}
        for hit in damage_events(payload):
            if (
                hit.actor == hit.target
                or is_healing_skill(hit.skill)
                or (hit.actor, hit.target, hit.skill) in healing_pairs
            ):
                continue
            self.event_count += 1
            self.publish("hit", (hit, now))

    def diagnostics(self):

        try:
            streams = list(self.streams.values())
        except RuntimeError:
            streams = []
        return {
            "packets": self.packet_count,
            "bytes": self.payload_bytes,
            "frames": self.frame_count,
            "damage_events": self.event_count,
            "heal_events": self.heal_count,
            "incoming_events": self.incoming_count,
            "listener_restarts": self.listener_restarts,
            "queue_dropped": self.dropped,
            "kernel_dropped": self.kernel_dropped,
            "parse_errors": sum(s.framer.errors for s in streams),
            "sync_skipped": sum(s.framer.skipped for s in streams),
            "tcp_resets": sum(s.resets for s in streams),
        }

    def stop(self):
        self.stop_event.set()
