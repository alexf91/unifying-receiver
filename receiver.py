from __future__ import print_function
import sys
import threading
import Queue
import datetime
import time
import argparse
import json

import numpy as np

import flowgraph

class ShockburstPacket(object):
    def __init__(self, packstr):
        self.addr    = hex(int(packstr[0:40], 2))[2:].zfill(10)
        self.length  = int(packstr[40:46], 2)
        self.pid     = int(packstr[46:48], 2)
        self.noack   = int(packstr[48])
        try:
            self.payload = hex(int(packstr[49:-16], 2))[2:].zfill(2*self.length)
        except ValueError:
            self.payload = ''
        self.crc     = hex(int(packstr[-16:], 2))

    def __str__(self):
        return '<{} - {} - {} - {} - {} - {}>'.format(
            self.addr,
            self.length,
            self.pid,
            self.noack,
            self.payload,
            self.crc
        )


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', type=str, help='Output JSON file', default=None)
    parser.add_argument('--lock', '-l', type=float, default=0.5,
        help='Time to lock on each channel while scanning')
    parser.add_argument('--timeout', '-t', type=float, default=2,
        help='Timeout after the last packet was received')
    parser.add_argument('--scantime', '-s', type=float, default=None,
        help='Time to scan in seconds. Defaults to infinity')

    args = parser.parse_args()

    channel = 0
    queue = Queue.Queue()

    tb = flowgraph.TopBlock(queue)
    tb.start()
    tb.set_frequency(flowgraph.channels[channel])

    starttime = datetime.datetime.now()
    print('\rListening on channel {}'.format(channel))

    timeout = args.lock
    packets = dict()

    if args.scantime is None:
        loopcond = lambda: True
    else:
        endtime  = time.time() + args.scantime
        loopcond = lambda: time.time() < endtime

    while loopcond():
        try:
            packet = queue.get(timeout=timeout)
            timeout = args.timeout
            packstr = ''.join([str(b) for b in packet])
            addr = hex(int(packstr[0:40], 2))
            shock = ShockburstPacket(packstr)
            print(shock)
            if not addr in packets:
                packets[addr] = [shock]
            else:
                packets[addr].append(shock)
        except Queue.Empty:
            channel = (channel + 1) % len(flowgraph.channels)
            tb.set_frequency(flowgraph.channels[channel])
            timeout = args.lock
            print('\rListening on channel {}'.format(channel))
        except KeyboardInterrupt:
            break

    stoptime = datetime.datetime.now()
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    sys.exit(main() or 0)
