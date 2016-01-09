from __future__ import print_function
import sys
import threading
import Queue
import datetime
import time
import argparse
import socket

import numpy as np

import flowgraph

def binstr_to_bytearray(binstr, length):
    if len(binstr) != 0:
        i = int(binstr, 2)
        hexstr = hex(i)[2:]
        if hexstr[-1] == 'L':
            hexstr = hexstr[0:-1]

        return bytearray.fromhex(hexstr.zfill(length*2))
    else:
        return bytearray(length)


def udp_datagram(channel, packstr):
    """
    Creates a datagram which can be sent to Wireshark.
    Format is <channel - address - length - pid - noack - payload - crc>
    with size     1    +    5    +    1   +  1  +   1   +    32   +  2    = 43  bytes
    """
    addr   = packstr[0:40]
    length = packstr[40:46]
    pid    = packstr[46:48]
    noack  = packstr[48]
    pld    = packstr[49:-16]
    crc    = packstr[-16:]

    dgram = bytearray(1 + 5 + 1 + 1 + 1 + 32 + 2)
    dgram[0]      = channel
    dgram[1:6]    = binstr_to_bytearray(addr, 5)
    dgram[6]      = int(length, 2)
    dgram[7]      = int(pid, 2)
    dgram[8]      = int(noack, 2)
    dgram[9:9+32] = binstr_to_bytearray(pld, 32)
    dgram[-2:]    = binstr_to_bytearray(crc, 2)
    
    return dgram

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', type=int, choices=range(1, 2**16), default=48222)
    parser.add_argument('--lock', '-l', type=float, default=0.5,
        help='Time to lock on each channel while scanning')
    parser.add_argument('--timeout', '-t', type=float, default=2,
        help='Timeout after the last packet was received')
    parser.add_argument('--scantime', '-s', type=float, default=None,
        help='Time to scan in seconds. Defaults to infinity')

    args = parser.parse_args()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    channel = 0
    queue = Queue.Queue()

    tb = flowgraph.TopBlock(queue)
    tb.start()
    tb.set_frequency(flowgraph.channels[channel])

    starttime = datetime.datetime.now()

    timeout = args.lock

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

            dgram = udp_datagram(channel, packstr)
            sock.sendto(dgram, ('127.0.0.1', args.port))
        except Queue.Empty:
            channel = (channel + 1) % len(flowgraph.channels)
            tb.set_frequency(flowgraph.channels[channel])
            timeout = args.lock
        except KeyboardInterrupt:
            break

    stoptime = datetime.datetime.now()
    tb.stop()
    tb.wait()

if __name__ == '__main__':
    sys.exit(main() or 0)
