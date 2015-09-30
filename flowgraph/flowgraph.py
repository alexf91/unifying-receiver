#!/usr/bin/python2

import math
import threading
from Queue import Queue, Empty

from gnuradio import blocks
from gnuradio import filter
from gnuradio import analog
from gnuradio import digital
from gnuradio import gr
import osmosdr
import sampling

import numpy as np


class TopBlock(gr.top_block):
    """
    Prefilter the raw IQ stream and convert it to possible packets,
    which get put into queue for further analysis.
    """
    def __init__(self, center_freq, queue):
        gr.top_block.__init__(self)

        self.queue = queue

        samp_rate = 18000000
        bandwidth = 2500000
        sharpness = 300000
        offset    = 3500000
        fsk_deviation = 300000
        resamp_rate = 18000000
        samp_per_symb = resamp_rate // 2000000

        # BladeRF source
        self.source = osmosdr.source('bladerf=0')
        self.source.set_sample_rate(samp_rate)
        self.source.set_center_freq(center_freq, 0)
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

        self.tagged_sink = blocks.tagged_file_sink(gr.sizeof_char*1, resamp_rate)
        self.connect(self.tagger, (self.tagged_sink, 0))

class SymbolRecovery(gr.basic_block):
    """
    Read stream of samples and generate symbols by
    simply sampling at samp_per_symb//2
    """
    def __init__(self, samp_per_symb):
        gr.basic_block.__init__(self,
            name='SymbolRecovery',
            in_sig=[np.byte],
            out_sig=[np.byte])

        self.samp_per_symb = samp_per_symb
        self.counter = 0
        self.last = 0

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        produced = 0
        consumed = 0
        for bit in in0:
            if bit != self.last:
                self.counter = 0
            self.counter += 1

            if self.counter % self.samp_per_symb == self.samp_per_symb//2:
                out[produced] = bit
                produced += 1

            self.last = bit
            consumed += 1

            if produced == out.size:
                break

        self.consume(0, consumed)
        return produced


class PacketSink(gr.sync_block):
    """
    Detects possible packets with a given preamble and output
    blocks of size packetsize to queue for analysis outside of
    gnuradio.
    """
    def __init__(self, packetsize, queue, preamble='01010101'):
        gr.sync_block.__init__(self, name='PacketDetector', in_sig=[np.byte], out_sig=None)
        self.packetsize = packetsize
        self.queue = queue

        self.preamble = np.array([int(x) for x in preamble], dtype=np.byte)

        self.backlog = np.zeros(len(preamble), dtype=np.byte)
        self.packets = []

    def work(self, input_items, output_items):
        in0 = input_items[0]

        for sample in in0:
            self._process_sample(sample)

        return len(input_items[0])

    def _process_sample(self, sample):
        self.backlog = np.roll(self.backlog, -1)
        self.backlog[-1] = sample

        if np.all(self.backlog == self.preamble):
            self.backlog = np.zeros(self.preamble.size, dtype=np.byte)
            packet = np.zeros(self.packetsize, dtype=np.byte)
            packet[:self.preamble.size-1] = self.preamble[:-1]
            self.packets.append((self.preamble.size-1, packet))

        for i, (index, packet) in enumerate(self.packets):
            packet[index] = sample
            index += 1

            if index == self.packetsize:
                self.queue.put(packet)
                del self.packets[i]
            else:
                self.packets[i] = (index, packet)


class Printer(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.running = True
        self.queue = queue

    def run(self):
        while self.running:
            try:
                packet = queue.get(timeout=0.1)
                print(''.join([str(x) for x in packet]))
            except Empty:
                pass

    def stop(self):
        self.running = False


if __name__ == '__main__':
    queue = Queue()
    printer = Printer(queue)
    printer.start()
    top = TopBlock(2458500000, queue)
    top.run()
    printer.stop()

