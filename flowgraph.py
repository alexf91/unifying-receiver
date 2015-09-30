#!/usr/bin/python2

import math
import threading
import datetime
from Queue import Queue, Empty

from gnuradio import blocks
from gnuradio import filter
from gnuradio import analog
from gnuradio import digital
from gnuradio import gr
import osmosdr

from bitarray import bitarray
import numpy as np


class TopBlock(gr.top_block):
    """
    Prefilter the raw IQ stream and convert it to possible packets,
    which get put into queue for further analysis.
    """
    def __init__(self, queue):
        gr.top_block.__init__(self)

        self.queue = queue

        samp_rate = 18000000
        bandwidth = 3000000
        sharpness = 300000
        offset    = 3500000
        fsk_deviation = 300000
        resamp_rate = 18000000
        samp_per_symb = resamp_rate // 2000000

        # BladeRF source
        self.source = osmosdr.source('bladerf=0')
        self.source.set_sample_rate(samp_rate)
        self.source.set_center_freq(2400000000, 0)
        self.source.set_bandwidth(samp_rate)
        #self.source.set_gain(10, 0)
        #self.source.set_if_gain(20, 0)
        #self.source.set_bb_gain(20, 0)

        # Mix to baseband
        lowpass = filter.firdes.low_pass(samp_rate / resamp_rate, samp_rate, bandwidth, sharpness)
        self.rf_filter = filter.freq_xlating_fir_filter_ccc(1, lowpass, offset, samp_rate)
        self.connect(self.source, (self.rf_filter, 0))

        # Quadrature demodulation
        self.demod = analog.quadrature_demod_cf(samp_rate/(2*math.pi*fsk_deviation/8.0))
        self.connect(self.rf_filter, (self.demod, 0))

        # Binary slicer
        self.slicer = digital.binary_slicer_fb()
        self.connect(self.demod, (self.slicer, 0))

        # Detect the carrier
        self.mag = blocks.complex_to_mag(1)
        self.connect(self.rf_filter, (self.mag, 0))

        # Floating average
        self.avg = blocks.moving_average_ff(50, 1/50., 4000)
        self.connect(self.mag, (self.avg, 0))

        # Subtract some offset
        self.offset = blocks.add_const_vff((-0.01, ))
        self.connect(self.avg, (self.offset, 0))

        # Binary signal from carrier
        self.carrier_slicer = digital.binary_slicer_fb()
        self.connect(self.offset, (self.carrier_slicer, 0))

        # Burst tagger needs short
        self.conv =  blocks.char_to_short(1)
        self.connect(self.carrier_slicer, (self.conv, 0))

        self.tagger = blocks.burst_tagger(gr.sizeof_char)
        self.tagger.set_true_tag("burst",True)
        self.tagger.set_false_tag("burst",False)
        self.connect(self.slicer, (self.tagger, 0))
        self.connect(self.conv, (self.tagger, 1))

        #self.tagged_sink = blocks.tagged_file_sink(gr.sizeof_char*1, resamp_rate)
        #self.connect(self.tagger, (self.tagged_sink, 0))
        self.packet_sink = RawPacketSink(samp_per_symb, self.queue, 500)
        self.connect(self.tagger, (self.packet_sink, 0))

    def set_frequency(self, frequency):
        self.source.set_center_freq(frequency, 0)

class RawPacketSink(gr.sync_block):
    """
    Detect 'burst' packets with a minimum length of 'minlength' samples and
    output them into the queue for further processing.
    """
    def __init__(self, samp_per_symb, queue, min_length=0):
        gr.sync_block.__init__(self, name='PacketDetector', in_sig=[np.byte], out_sig=None)
        self.samp_per_symb = samp_per_symb
        self.queue = queue
        self.min_length = min_length

        self.decoding = False

        self.samp_counter = 0
        self.last_sample = 0
        self.samp_processed = 0
        self.symbols = bitarray()

    def work(self, input_items, output_items):
        in0 = input_items[0]

        regions = self.create_regions(in0.size)

        for start, stop, done in regions:
            if self.samp_processed == 0 and (stop - start) < self.min_length:
                continue

            for i in range(start, stop):
                bit = in0[i]
                if self.last_sample != bit:
                    self.samp_counter = 0

                self.samp_counter += 1
                if self.samp_counter % self.samp_per_symb == self.samp_per_symb//2:
                    self.symbols.append(bit)

                self.last_sample = bit

            self.samp_processed += (stop - start)

            if done:
                self.samp_processed = 0
                self.samp_counter = 0
                self.queue.put(self.symbols.copy())
                self.symbols = bitarray()
                self.last_sample = 0

        return in0.size

    def create_regions(self, nitems):
        nread = self.nitems_read(0) #number of items read on port 0
        tags = map(gr.tag_to_python, self.get_tags_in_range(0, nread, nread+nitems))
        regions = []
        decoding = self.decoding

        start = 0
        for tag in tags:
            if decoding:
                assert not tag.value
                stop = tag.offset - nread
                assert stop >= 0
                regions.append((start, stop, True))
                decoding = False
            else:
                assert tag.value
                start = tag.offset - nread
                assert start >= 0
                decoding = True

        if decoding:
            stop = nitems
            regions.append((start, stop, False))

        self.decoding = decoding
        return regions




if __name__ == '__main__':
    queue = Queue()
    printer = Printer(queue)
    printer.start()
    receiver = TopBlock(queue)
    receiver.set_frequency(2431500000)
    receiver.run()
    printer.stop()

