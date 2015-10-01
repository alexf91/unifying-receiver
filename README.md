# unifying-receiver

An attempt to reverse-engineer the protocol of Logitechs Unifying Receiver technology.

The project is intended to work with BladeRF SDR. Signal processing is carried out with
GNU Radio.

## Progress
* Automatic search for the frequency used
* Decoding of the low-level protocol (Nordic Semiconductor Enhanced Shockburst)

## Protocol
* 5 byte address
* 2 byte CRC

It looks like that the address is assigned during pairing, with the first 36 bits
being static between all devices paired with one receiver and the last 4 bits
different for each device.

## Pointing devices
Pointing devices like mouses and trackballs send 10 byte long packets on
movements or clicks:

00 C2 Buttons 00 X-speed Y-speed <00 or FF> 00 00 <unknown>

## Keyboard devices
Keyboard devices are encrypted and probably can't be sniffed.

## TODO:
* Rework the Shockburst packet class
* Rework the flowgraph, especially the carrier detection. Currently, the sensitivity is
  way worse than that of the original receiver and the flowgraph contains some hardcoded values.
