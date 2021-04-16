from bof import BOFPacket
from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1


class BOFBasicOtterPacket1(BOFPacket):
    name = "BOFBasicOtterPacket1"

    def __init__(self, scapy_pkt=ScapyBasicOtterPacket1()):
        self.scapy_pkt = scapy_pkt
