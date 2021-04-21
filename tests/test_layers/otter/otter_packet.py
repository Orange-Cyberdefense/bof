from bof import BOFPacket
from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1


class BOFBasicOtterPacket1(BOFPacket):
    name = "BOFBasicOtterPacket1"

    def __init__(self, _pkt:bytes=None,
                 scapy_pkt:Packet=ScapyBasicOtterPacket1(), **kwargs):
        super().__init__(_pkt, scapy_pkt, **kwargs)
