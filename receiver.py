#!/usr/bin/env python2

import sys
import argparse
import threading
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
    def __init__(self, raw_queue, packet_queue):
        threading.Thread.__init__(self)
        self.running = True
        self.raw_queue = raw_queue
        self.packet_queue = packet_queue

    def run(self):
        while self.running:
            try:
                raw = self.raw_queue.get(timeout=0.1)
                packet = shockburst.EnhancedShockburstPacket.from_bitarray(
                    raw, addr_len=5, crc_len=2, raw=True, tries=8)

                self.packet_queue.put(packet)
            except (shockburst.ShockburstError, Empty):
                pass

    def stop(self):
        self.running = False

def main():
    # Raw packets from flowgraph to packet decoder
    raw_queue = Queue()

    # Decoded packets from decoder to printer
    packet_queue = Queue()

    receiver = flowgraph.TopBlock(raw_queue)
    receiver.set_frequency(2428500000)
    decoder =  Decoder(raw_queue, packet_queue)
    printer = Printer(packet_queue)

    decoder.start()
    printer.start()
    receiver.run()
    decoder.stop()
    printer.stop()

if __name__ == '__main__':
    sys.exit(main() or 0)

