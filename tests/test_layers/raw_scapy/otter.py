from scapy.fields import ByteField
from scapy.packet import Packet


class ScapyBasicOtterPacket1(Packet):
    name = "basic_otter_packet_1"
    fields_desc = [
        ByteField("basic_otter_1_1", 0x01),
        ByteField("basic_otter_1_2", 0x02)
    ]


class ScapyBasicOtterPacket2(Packet):
    name = "basic_otter_packet_2"
    fields_desc = [
        ByteField("basic_otter_2_1", 0x01),
        ByteField("basic_otter_2_2", 0x02)
    ]
