#!/usr/bin/env python2

import argparse
import threading
from Queue import Queue, Empty

import flowgraph
import shockburst


def main():
    # Raw packets from flowgraph to packet decoder
    raw_queue = Queue()

    # Decoded packets from decoder to printer
    packet_queue = Queue()

    receiver = flowgraph.TopLevel(raw_queue)

if __name__ == '__main__':
    sys.exit(main() or 0)

