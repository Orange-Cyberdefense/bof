# TODO: class documentation
from bof.layers.raw_scapy.knx import KNXHeader
from bof.packet import BOFPacket


class KNXBOFPacket(BOFPacket):
    def __init__(self):
        self.scapy_pkt = KNXHeader()
