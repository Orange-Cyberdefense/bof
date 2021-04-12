"""TODO
"""

from bof.layers.raw_scapy.knx import KNX as ScapyKNX
from bof.packet import BOFPacket


class KNX(BOFPacket):
    def __init__(self, _pkt:bytes=None):
        self.scapy_pkt = ScapyKNX(_pkt=_pkt)
