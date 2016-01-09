#!/usr/bin/python2

import threading

from gnuradio import blocks
from gnuradio import filter
from gnuradio import analog
from gnuradio import digital
from gnuradio import gr
import osmosdr

import numpy as np
import Queue

channels = [2403000000, 2406000000, 2409000000, 2412000000, 2415000000,
            2418000000, 2421000000, 2424000000, 2427000000, 2431500000,
            2433000000, 2436000000, 2439000000, 2442000000, 2445000000,
            2448000000, 2451000000, 2454000000, 2457000000, 2460000000,
            2463000000, 2466000000, 2469000000, 2472000000, 2475000000]

def array_to_int(array):
    x = 0
    for b in array:
        x = 2*x + b

    return x

class Deframer(gr.sync_block):
    def __init__(self, queue):
        gr.sync_block.__init__(self, name='PacketDetector', in_sig=[np.byte], out_sig=None)
        self.buffer  = np.int8([])
        self.queue = queue

    def work(self, input_items, output_items):
        nread = self.nitems_read(0) #number of items read on port 0
        in0 = input_items[0]
        
        tags = map(gr.tag_to_python, self.get_tags_in_range(0, nread, nread+in0.size))

        for tag in tags:
            start = tag.offset - nread

            packet = np.concatenate((self.buffer, in0[start:start+340-self.buffer.size]))
            self.buffer = np.int8([])

            if packet.size != 340:
                self.buffer = packet
            else:
                packet = np.concatenate((np.array([0,1], dtype=np.int8), packet))
                packet = self.valid_packet(packet)
                if packet is not None:
                    self.queue.put(packet)
        
        return in0.size

    def valid_packet(self, packet):

        length = array_to_int(packet[40:46])
        if length > 32:
            return None

        packet = packet[0:8*5 + 9 + length*8 + 16]

        crc_calc = self.crc16(packet[0:-16])
        crc_pack = array_to_int(packet[-16:])
        
        if crc_calc == crc_pack:
            return packet
        else:
            return None

    def crc16(self, packet):
        poly = 0x11021
        crc = 0xFFFF
        for bit in packet:
            if (crc >> 15) & 0x01 != int(bit):
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

        return crc

class TopBlock(gr.top_block):
    SAMP_RATE   = 8000000
    CENTER_FREQ = 2000000
    SAMP_PER_SYMB = 4
    FILTER_BANDWIDTH = 1500000
    FILTER_SHARPNESS = 100000

    def __init__(self, queue):
        gr.top_block.__init__(self)

        self.osmosrc = osmosdr.source('bladerf=0')
        self.osmosrc.set_sample_rate(self.SAMP_RATE)
        self.osmosrc.set_center_freq(2400000000, 0)
        self.osmosrc.set_bandwidth(self.SAMP_RATE)

        lowpass = filter.firdes.low_pass(1, self.SAMP_RATE, self.FILTER_BANDWIDTH, self.FILTER_SHARPNESS)
        self.xlating = filter.freq_xlating_fir_filter_ccc(2, lowpass, self.CENTER_FREQ, self.SAMP_RATE)

        self.gfsk_demod = digital.gfsk_demod(
            samples_per_symbol=2,
            sensitivity=1.0,
            gain_mu=0.175,
            mu=0.5,
            omega_relative_limit=0.005,
            freq_error=0.0,
            verbose=False,
            log=False,
        )

        self.correlate = digital.correlate_access_code_tag_bb('01010101', 0, 'burst')
        self.deframer  = Deframer(queue)

        self.connect((self.osmosrc, 0), (self.xlating, 0))
        self.connect((self.xlating, 0), (self.gfsk_demod, 0))
        self.connect((self.gfsk_demod, 0), (self.correlate, 0))
        self.connect((self.correlate, 0), (self.deframer, 0))

    def set_frequency(self, frequency):
        self.osmosrc.set_center_freq(frequency, 0)
