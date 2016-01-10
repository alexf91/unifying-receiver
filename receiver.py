from __future__ import print_function
import sys
import Queue
import time
import argparse
import subprocess
import ctypes

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

class PcapFileHeader(ctypes.Structure):
    _fields_ = [
        ('magic_number',  ctypes.c_uint32),
        ('version_major', ctypes.c_uint16),
        ('version_minor', ctypes.c_uint16),
        ('thiszone',      ctypes.c_uint32),
        ('sigfigs',       ctypes.c_uint32),
        ('snaplen',       ctypes.c_uint32),
        ('network',       ctypes.c_uint32),
    ]

    def __init__(self, linktype):
        ctypes.Structure.__init__(self)
        self.magic_number = 0xa1b2c3d4
        self.version_major = 2
        self.version_minor = 4
        self.thiszone = 0
        self.sigfigs = 0
        self.snaplen = 2**16
        self.network = linktype

class PcapPacketHeader(ctypes.Structure):
    _fields_ = [
        ('ts_sec',   ctypes.c_uint32),
        ('ts_usec',  ctypes.c_uint32),
        ('incl_len', ctypes.c_uint32),
        ('orig_len', ctypes.c_uint32),
    ]
        
def pcap_write(fileobj, channel, packstr):
    addr   = binstr_to_bytearray(packstr[0:40], 5)
    length = int(packstr[40:46], 2)
    pid    = int(packstr[46:48], 2)
    noack  = int(packstr[48], 2)
    pld    = binstr_to_bytearray(packstr[49:-16], length)
    crc    = binstr_to_bytearray(packstr[-16:], 2)
    
    hdr = PcapPacketHeader()
    t = time.time()
    hdr.ts_sec  = int(t)
    hdr.ts_usec = int((t % 1) * 1000000)
    pkglen = 1 + 5 + 1 + 1 + length + 2
    hdr.incl_len = pkglen
    hdr.orig_len = pkglen

    dgram       = bytearray(pkglen)
    dgram[0]    = channel
    dgram[1:6]  = addr
    dgram[6]    = pid
    dgram[7]    = noack
    dgram[8:-2] = pld
    dgram[-2:]  = crc

    fileobj.write(hdr)
    fileobj.write(dgram)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lock', '-l', type=float, default=0.5,
        help='Time to lock on each channel while scanning')
    parser.add_argument('--timeout', '-t', type=float, default=2,
        help='Timeout after the last packet was received')
    parser.add_argument('--scantime', '-s', type=float, default=None,
        help='Time to scan in seconds. Defaults to infinity')

    args = parser.parse_args()

    channel = 0
    queue = Queue.Queue()

    wireshark = subprocess.Popen('wireshark-gtk -k -i -'.split(), stdin=subprocess.PIPE)
    wireshark.stdin.write(PcapFileHeader(147))

    tb = flowgraph.TopBlock(queue)
    tb.start()
    tb.set_frequency(flowgraph.channels[channel])

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

            try:
                pcap_write(wireshark.stdin, channel, packstr)
            except IOError:
                break
        except Queue.Empty:
            channel = (channel + 1) % len(flowgraph.channels)
            tb.set_frequency(flowgraph.channels[channel])
            timeout = args.lock
        except KeyboardInterrupt:
            break

    tb.stop()
    tb.wait()

if __name__ == '__main__':
    sys.exit(main() or 0)
