from scapy.fields import ByteField
from scapy.layers.inet import TCP
from scapy.packet import Packet, bind_layers


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


class ScapyBasicOtterPacket3(Packet):
    name = "basic_otter_packet_3"
    fields_desc = [
        ByteField("basic_otter_3_1", 0x01),
        ByteField("basic_otter_3_2", 0x02)
    ]


class ScapyBasicOtterPacket4(Packet):
    name = "basic_otter_packet_4"
    fields_desc = [
        ByteField("basic_otter_4_1", 0x01),
        ByteField("basic_otter_4_2", 0x02)
    ]


bind_layers(ScapyBasicOtterPacket1, ScapyBasicOtterPacket2)
bind_layers(ScapyBasicOtterPacket2, ScapyBasicOtterPacket4)
