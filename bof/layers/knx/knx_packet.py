"""TODO
"""

from bof.layers.raw_scapy import knx as scapy_knx
from bof.packet import BOFPacket


class KNX(BOFPacket):
    def __init__(self, _pkt:bytes=None, type=None):
        self.scapy_pkt = scapy_knx.KNX(_pkt=_pkt)
