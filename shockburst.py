#!/usr/bin/env python2

from bitarray import bitarray

class ShockburstError(Exception):
    pass

class EnhancedShockburstConfig(object):
    addressLength = property(lambda self: self._addressLength)
    crcLength     = property(lambda self: self._crcLength)

    def __init__(self, addressLength, crcLength):
        self._addressLength = addressLength
        self._crcLength = crcLength

class EnhancedShockburstPacket(object):
    """
    An Enhanced Shockburst packet
    """
    def __init__(self, address, payload, crc, pid=0, noack=0):
        """
        Initializes a new Enhanced Shockburst packet.
        Types: address : bytes
               payload : bytes
               pid     : integer
               noack   : integer
               crc     : bytes

        This method should not be called by the user.
        Packets should be created with the classmethods.
        """

        if len(payload) > 32:
            raise ShockburstError('Payload too long')

        if not (0 <= pid <= 3):
            raise ShockburstError('Invalid packet ID')

        packet = bitarray()
        packet.frombytes(address)
        packet.extend(bin(len(payload))[2:].zfill(6))
        packet.extend(bin(pid)[2:].zfill(2))
        packet.extend(str(int(noack)))
        packet.frombytes(payload)
        packet.frombytes(crc)

        self._packet = packet

    @classmethod
    def from_bitarray(cls, bitstream, addr_len=5, crc_len=2, raw=False, tries=4):
        """
        Create a packet from a bitarray. If raw is set,
        the multiple preambles are searched and tested.
        """
        preamble = bitarray('01010101')

        if raw:
            results = bitstream.search(preamble)
        else:
            results = [0]

        for idx in results[:tries]:
            addr_idx = idx + len(preamble)
            size_idx = addr_idx + addr_len*8
            pid_idx  = size_idx + 6
            noack_idx = pid_idx + 2
            pld_idx  = pid_idx + 1
            size = int(bitstream[size_idx:size_idx+6].to01(), 2)
            crc_idx  = pld_idx + size*8

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
                raise ShockburstError('Wrong CRC length')

            if calc_crc != crc:
                continue

            crc = crc.tobytes()
            return cls(address, payload, crc, pid, noack)

        raise ShockburstError('No valid packet found')

    def __str__(self):
        return self._packet.to01()


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
    packet = EnhancedShockburstPacket.from_bitarray(bitarray(msg), addr_len=5, crc_len=2, raw=True, tries=8)
    print(packet)







