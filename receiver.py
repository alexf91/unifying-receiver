#!/usr/bin/env python2

import sys
import argparse
import threading
from datetime import datetime, timedelta
from Queue import Queue, Empty

import flowgraph
import shockburst

class Printer(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.running = True
        self.queue = queue

    def run(self):
        while self.running:
            try:
                packet = self.queue.get(timeout=0.1)
                print(packet)
            except Empty:
                pass

    def stop(self):
        self.running = False

class Decoder(threading.Thread):
    def __init__(self, raw_queue, packet_queue, set_freq_fnc=None, locked_timeout=2,
                 sweep_timeout=1):
        threading.Thread.__init__(self)
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

def main():
    # Raw packets from flowgraph to packet decoder
    raw_queue = Queue()

    # Decoded packets from decoder to printer
    packet_queue = Queue()

    receiver = flowgraph.TopBlock(raw_queue)
    decoder =  Decoder(raw_queue, packet_queue, sweep_timeout=0.1,
                       set_freq_fnc=receiver.set_frequency, locked_timeout=10)
    printer = Printer(packet_queue)

    decoder.start()
    printer.start()
    receiver.run()
    decoder.stop()
    printer.stop()

if __name__ == '__main__':
    sys.exit(main() or 0)

