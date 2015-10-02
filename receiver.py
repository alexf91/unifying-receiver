#!/usr/bin/env python2

import sys
import argparse
from Queue import Queue, Empty

import flowgraph
import blocks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--channel-time', default=0.2, type=float,
                        help='Time for each channel while searching')
    parser.add_argument('-t', '--timeout', default=5, type=float,
                        help='Timeout until searching starts again')
    parser.add_argument('-e', '--exclude', default=None, type=str,
                        help='Exclude given addresses (comma seperated)')
    parser.add_argument('-i', '--include', default=None, type=str,
                        help='Include given addresses (comma seperated)')
    parser.add_argument('--ignore-ack', action='store_true',
                        help='Ignore packets with empty payload')
    parser.add_argument('-s', '--squelch', type=int, default=-30)

    args = parser.parse_args()

    if args.exclude and args.include:
        print("--exclude and --include can't be used together")
        return 1

    if args.exclude is not None:
        args.exclude = args.exclude.split(',')

    if args.include is not None:
        args.include = args.include.split(',')

    # Raw packets from flowgraph to packet decoder
    raw_queue = Queue()

    # Decoded packets from decoder to printer
    packet_queue = Queue()

    receiver = flowgraph.TopBlock(raw_queue, args.squelch)
    decoder = blocks.Decoder(raw_queue, packet_queue, sweep_timeout=args.channel_time,
                             set_freq_fnc=receiver.set_frequency, locked_timeout=args.timeout)

    duplicator = blocks.Duplicator(packet_queue)
    printer_queue = Queue()
    printer = blocks.Printer(printer_queue, args.exclude, args.include, args.ignore_ack)
    duplicator.connect(printer_queue)

    decoder.start()
    printer.start()
    duplicator.start()
    receiver.run()

    decoder.stop()
    printer.stop()
    duplicator.stop()

if __name__ == '__main__':
    sys.exit(main() or 0)

