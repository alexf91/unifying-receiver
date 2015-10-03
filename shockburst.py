#!/usr/bin/env python2

from bitarray import bitarray

class PacketError(Exception):
    pass

class Packet(object):
    """
    An Enhanced Shockburst packet
    """

    address = property(lambda self: self._address[:])
    payload = property(lambda self: self._payload[:])
    crc     = property(lambda self: self._crc[:])
    pid     = property(lambda self: self._pid)
    noack   = property(lambda self: self._noack)
    size    = property(lambda self: self._size)

    def __init__(self, address, payload, crc, pid=0, noack=0):
        """
        Initializes a new Enhanced Shockburst packet.
        Types: address : bytearray or bytes
               payload : bytearray or bytes
               pid     : integer
               noack   : integer
               crc     : bytearray or bytes

        This method should not be called by the user.
        Packets should be created with the classmethods.
        """

        if len(payload) > 32:
            raise PacketError('Payload too long')

        if not (0 <= pid <= 3):
            raise PacketError('Invalid packet ID')

        self._address = bytearray(address)
        self._payload = bytearray(payload)
        self._crc = bytearray(crc)
        self._pid = int(pid)
        self._noack = int(bool(noack))
        self._size = len(payload)

    @classmethod
    def from_bitarray(cls, bitstream, addr_len=5, crc_len=2, raw=False, tries=4):
        """
        Create a packet from a bitarray. If raw is set,
        multiple preambles are tried as the beginning of the packet.
        """
        preamble = bitarray('010101')

        if raw:
            results = bitstream.search(preamble)
        else:
            results = [0]

        for idx in results[:tries]:
            addr_idx = idx + len(preamble)
            size_idx = addr_idx + addr_len*8
            pid_idx  = size_idx + 6
            noack_idx = pid_idx + 2
            pld_idx  = noack_idx + 1
            try:
                size = int(bitstream[size_idx:size_idx+6].to01(), 2)
            except:
                continue

            crc_idx  = pld_idx + size*8

            if len(bitstream[addr_idx:crc_idx+crc_len*8]) != (crc_idx+crc_len*8 - addr_idx):
                continue

            address = bitstream[addr_idx : size_idx].tobytes()
            pid     = int(bitstream[pid_idx : pid_idx+2].to01(), 2)
            noack   = int(bitstream[noack_idx])
            payload = bitstream[pld_idx : crc_idx].tobytes()
            crc     = bitstream[crc_idx : crc_idx+crc_len*8]

            if crc_len == 1:
                calc_crc = cls.crc8(bitstream[addr_idx : crc_idx])
            elif crc_len == 2:
                calc_crc = cls.crc16(bitstream[addr_idx : crc_idx])
            else:
                raise PacketError('Wrong CRC length')

            if calc_crc != crc:
                continue

            crc = crc.tobytes()
            return cls(address, payload, crc, pid, noack)

        raise PacketError('No valid packet found')

    def __str__(self):
        address  = ''.join([hex(x)[2:].zfill(2) for x in self.address])
        if self.size:
            payload  = ' '.join([hex(x)[2:].zfill(2) for x in self.payload])
        else:
            payload = 'ACK'

        return '{}-{} - {}'.format(address, self.pid, payload)

    @staticmethod
    def crc8(bitstream):
        poly = 0x107
        crc = 0xFF
        for bit in bitstream:
            if (crc >> 7) & 0x01 != int(bit):
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

        return bitarray(bin(crc)[2:].zfill(8))

    @staticmethod
    def crc16(bitstream):
        poly = 0x11021
        crc = 0xFFFF
        for bit in bitstream:
            if (crc >> 15) & 0x01 != int(bit):
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

        return bitarray(bin(crc)[2:].zfill(16))



if __name__ == '__main__':
    msg = '010101010100111111101100100100000010100000001101001010100000000001100001000000000000000001111111111001111111111110000000000000000011100011000010110101100'
    packet = Packet.from_bitarray(bitarray(msg), addr_len=5, crc_len=2, raw=True, tries=8)
    print(packet)

