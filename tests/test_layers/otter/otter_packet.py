from scapy.packet import Packet

from bof import BOFPacket
from tests.test_layers.raw_scapy.otter import *


class BOFBasicOtterPacket1(BOFPacket):
    name = "BOFBasicOtterPacket1"

    def __init__(self, _pkt:bytes=None,
                 scapy_pkt:Packet=None, **kwargs):
        super().__init__(_pkt, scapy_pkt if scapy_pkt else ScapyBasicOtterPacket1(), **kwargs)

class BOFNestedOtterPacket1(BOFPacket):
    name = "BOFNestedOtterPacket1"

    def __init__(self, _pkt:bytes=None,
                 scapy_pkt:Packet=None, **kwargs):
        super().__init__(_pkt, scapy_pkt if scapy_pkt else ScapyNestedOtterPacket1(), **kwargs)
