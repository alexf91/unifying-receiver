import threading
from datetime import datetime, timedelta
from Queue import Queue, Empty
import enum

import shockburst


def bytes_to_hexstring(bytes, seperator=''):
    return seperator.join([hex(x)[2:].zfill(2) for x in bytes])

class Printer(threading.Thread):
    def __init__(self, queue, exclude=None, include=None, ignore_ack=False):
        threading.Thread.__init__(self, name='Printer')
        self.running = True
        self.queue = queue
        self.exclude = exclude
        self.include = include
        self.ignore_ack = ignore_ack

    def run(self):
        while self.running:
            try:
                packet = self.queue.get(timeout=0.1)
                address = bytes_to_hexstring(packet.address)
                if packet.size == 0 and self.ignore_ack:
                    continue

                if self.exclude and address in self.exclude:
                    continue

                if not self.include or address in self.include:
                    print(packet)

            except Empty:
                pass

    def stop(self):
        self.running = False


class Position(enum.Enum):
    begins = 0
    ends = 1
    contains = 2
    matches = 3

class Filter(object):
    def __init__(self, position, data, attribute):
        if isinstance(data, str):
            self.data = data
        elif isinstance(data, int):
            self.data = hex(data)[2:]
        else:
            raise ValueError('Invalid argument')

        self.position = position
        self.attribute = attribute

    def matches(self, packet):
        data = bytes_to_hexstring(getattr(packet, self.attribute))

        if self.position == Position.begins:
            return data.startswith(self.data)
        elif self.position == Position.ends:
            return data.endswith(self.data)
        elif self.position == Position.matches:
            return data == self.data
        elif self.position == Position.contains:
            return self.data in data
        else:
            return False

class PayloadFilter(Filter):
    def __init__(self, position, data):
        Filter.__init__(self, position, data, 'payload')


class Duplicator(threading.Thread):
    def __init__(self, inqueue, outqueues=[]):
        threading.Thread.__init__(self, name='Duplicator')
        self.inqueue = inqueue
        self.outqueues = outqueues
        self.running = True

    def run(self):
        while self.running:
            try:
                packet = self.inqueue.get(timeout=0.1)
            except:
                continue

            for queue in self.outqueues:
                queue.put(packet)

    def stop(self):
        self.running = False

    def connect(self, queue):
        self.outqueues.append(queue)


class Decoder(threading.Thread):
    def __init__(self, raw_queue, packet_queue, set_freq_fnc=None, locked_timeout=2,
                 sweep_timeout=1):
        threading.Thread.__init__(self, name='Decoder')
        self.running = True
        self.raw_queue = raw_queue
        self.packet_queue = packet_queue
        self.set_freq = set_freq_fnc
        self.locked_timeout = locked_timeout
        self.sweep_timeout = sweep_timeout

    def run(self):
        channels = [2401500000, 2404500000, 2407500000, 2410500000, 2413500000,
                    2416500000, 2419500000, 2422500000, 2425500000, 2428500000,
                    2431500000, 2434500000, 2437500000, 2440500000, 2443500000,
                    2446500000, 2449500000, 2452500000, 2455500000, 2458500000,
                    2461500000, 2464500000, 2467500000, 2470500000]

        freq_idx = 0
        last_recv = datetime.now()
        timeout = self.sweep_timeout
        if self.set_freq is not None:
            self.set_freq(channels[0])

        while self.running:
            try:
                raw = self.raw_queue.get(timeout=0.1)
                packet = shockburst.Packet.from_bitarray(
                    raw, addr_len=5, crc_len=2, raw=True, tries=8)

                self.packet_queue.put(packet)
                last_recv = datetime.now()
                timeout = self.locked_timeout
            except (Empty, shockburst.PacketError):
                pass

            if (datetime.now() - last_recv).total_seconds() > timeout and self.set_freq:
                freq_idx = (freq_idx + 1) % len(channels)
                self.set_freq(channels[freq_idx])
                print('Switching to channel {}'.format(freq_idx))
                last_recv = datetime.now()
                timeout = self.sweep_timeout

    def stop(self):
        self.running = False

