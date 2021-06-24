from scapy.fields import ByteField, PacketField
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

class ScapyNestedOtterPacket2(Packet):
    name = "nested_otter_packet_2"
    fields_desc = [
        PacketField("nested_otter_2_4", ScapyBasicOtterPacket4(), ScapyBasicOtterPacket4),
    ]

class ScapyNestedOtterPacket1(Packet):
    name = "nested_otter_packet_1"
    fields_desc = [
        PacketField("nested_otter_1_1", ScapyBasicOtterPacket1(), ScapyBasicOtterPacket1),
        PacketField("nested_otter_1_3", ScapyBasicOtterPacket3(), ScapyBasicOtterPacket3),
        PacketField("nested_otter", ScapyNestedOtterPacket2(), ScapyNestedOtterPacket2)
    ]

class ScapyOtterGuessPayloadPacket1(Packet):
    name = "guess_otter_1"
    fields_desc = [
        ByteField("payload_identifier", None)
    ]

    def guess_payload_class(self, payload):
        if self.payload_identifier == 0x01:
            return ScapyBasicOtterPacket1
        elif self.payload_identifier == 0x02:
            return ScapyBasicOtterPacket2
        else:
            return None

bind_layers(ScapyBasicOtterPacket1, ScapyBasicOtterPacket2)
bind_layers(ScapyBasicOtterPacket2, ScapyBasicOtterPacket4)
