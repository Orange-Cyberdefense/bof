from scapy.fields import PacketField, MultipleTypeField, ByteField, XByteField, ShortEnumField, ShortField, \
    ByteEnumField, IPField, StrFixedLenField, MACField, XBitField, PacketListField, IntField, FieldLenField, \
    StrLenField, BitEnumField, BitField, ConditionalField
from scapy.packet import Packet, bind_layers, Padding

### KNX CODES

SERVICE_IDENTIFIER_CODES = {
    0x0201: "SEARCH_REQUEST",
    0x0202: "SEARCH_RESPONSE",
    0x0203: "DESCRIPTION_REQUEST",
    0x0204: "DESCRIPTION_RESPONSE",
    0x0205: "CONNECT_REQUEST",
    0x0206: "CONNECT_RESPONSE",
    0x0207: "CONNECTIONSTATE_REQUEST",
    0x0208: "CONNECTIONSTATE_RESPONSE",
    0x0209: "DISCONNECT_REQUEST",
    0x020A: "DISCONNECT_RESPONSE",
    0x0310: "CONFIGURATION_REQUEST",
    0x0311: "CONFIGURATION_ACK",
    0x0420: "TUNNELING_REQUEST",
    0x0421: "TUNNELING_ACK"
}

HOST_PROTOCOL_CODES = {
    0x01: "IPV4_UDP"
}

DESCRIPTION_TYPE_CODES = {
    0x01: "DEVICE_INFO",
    0x02: "SUPP_SVC_FAMILIES"
}

# uses only 1 code collection for connection type, differentiates between CRI and CRD tunneling in classes (!= BOF)
CONNECTION_TYPE_CODES = {
    0x03: "DEVICE_MANAGEMENT_CONNECTION",
    0x04: "TUNNELING_CONNECTION"
}

MESSAGE_CODES = {
    0x11: "L_Data.req",
    0x2e: "L_Data.con",
    0xFC: "PropRead.req",
    0xFB: "PropRead.con",
    0xF6: "PropWrite.req",
    0xF5: "PropWrite.con"
}

KNX_MEDIUM_CODES = {
    0x02: "KNX_TP"
}

### KNX SPECIFIC FIELDS

class KNXAddressField(ShortField):
    def i2repr(self, pkt, x):
        if x is None:
            return None
        else:
            return "%d.%d.%d" % ((x >> 12) & 0xf, (x >> 8) & 0xf, (x & 0xff))

    def any2i(self, pkt, x):
        if type(x) is str:
            try:
                a, b, c = map(int, x.split("."))
                x = (a << 12) | (b << 8) | c
            except:
                raise ValueError(x)
        return ShortField.any2i(self, pkt, x)


class KNXGroupField(ShortField):
    def i2repr(self, pkt, x):
        return "%d/%d/%d" % ((x >> 11) & 0x1f, (x >> 8) & 0x7, (x & 0xff))

    def any2i(self, pkt, x):
        if type(x) is str:
            try:
                a, b, c = map(int, x.split("/"))
                x = (a << 11) | (b << 8) | c
            except:
                raise ValueError(x)
        return ShortField.any2i(self, pkt, x)


### KNX BASE BLOCKS


class HPAI(Packet):
    name = "HPAI"
    fields_desc = [
        ByteField("structure_length", None),
        ByteEnumField("host_protocol", 0x01, HOST_PROTOCOL_CODES),
        IPField("ip_address", None),
        ShortField("ip_port", None)
    ]

    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay


# DIB blocks

class ServiceFamily(Packet):
    name = "Service Family"
    fields_desc = [
        ByteField("id", None),
        ByteField("version", None)
    ]


# DIB are differentiated using the "description_type_code" field
# Defining a generic DIB packet and differentiating with `dispatch_hook` or `MultipleTypeField` may better fit KNX specs
class DIBDeviceInfo(Packet):
    name = "DIB: DEVICE_INFO"
    fields_desc = [
        ByteField("structure_length", None),
        ByteEnumField("description_type", 0x01, DESCRIPTION_TYPE_CODES),
        ByteEnumField("knx_medium", 0x02, KNX_MEDIUM_CODES),
        ByteField("device_status", None),
        KNXAddressField("knx_address", None),
        ShortField("project_installation_identifier", None),
        XBitField("device_serial_number", None, 48),
        IPField("device_multicast_address", None),
        MACField("device_mac_address", None),
        StrFixedLenField("device_friendly_name", None, 30)
    ]

    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay


class DIBSuppSvcFamilies(Packet):
    name = "DIB: SUPP_SVC_FAMILIES"
    fields_desc = [
        ByteField("structure_length", 0x02),
        ByteEnumField("description_type", 0x02, DESCRIPTION_TYPE_CODES),
        ConditionalField(PacketListField("service_family", ServiceFamily(), ServiceFamily,
                                         length_from=lambda pkt: pkt.structure_length - 0x02),
                         lambda pkt: pkt.structure_length > 0x02)
    ]

    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay


# CRI and CRD blocks

class DeviceManagementConnection(Packet):
    name = "Device Management Connection"
    fields_desc = [
        IntField("ip_address_1", None),
        ByteField("port_1", None),
        IntField("ip_address_2", None),
        ByteField("port_2", None)
    ]


class TunnelingConnection(Packet):
    name = "Tunneling Connection"
    fields_desc = [
        ByteField("knx_layer", 0x02),
        ByteField("reserved", None)
    ]


class CRDTunnelingConnection(Packet):
    name = "CRD Tunneling Connection"
    fields_desc = [
        KNXAddressField("knx_individual_address", None)
    ]


class CRI(Packet):
    name = "CRI (Connection Request Information)"
    fields_desc = [
        ByteField("structure_length", 0x00),
        ByteEnumField("connection_type", 0x03, CONNECTION_TYPE_CODES),
        MultipleTypeField(
            [
                # see in KNX specs if better than "pkt.structure_length > 0x02" to check if a body is present
                (PacketField("connection_data", DeviceManagementConnection(), DeviceManagementConnection),
                 lambda pkt: pkt.connection_type == 0x03 and pkt.structure_length > 0x02),
                (PacketField("connection_data", TunnelingConnection(), TunnelingConnection),
                 lambda pkt: pkt.connection_type == 0x04 and pkt.structure_length > 0x02)
            ],
            PacketField("connection_data", None, ByteField)
        )

    ]


class CRD(Packet):
    name = "CRD (Connection Response Data)"
    fields_desc = [
        ByteField("structure_length", 0x00),
        ByteEnumField("connection_type", 0x03, CONNECTION_TYPE_CODES),
        MultipleTypeField(
            [
                # see if better way than "pkt.structure_length > 0x02" to check if a body is present
                (PacketField("connection_data", DeviceManagementConnection(), DeviceManagementConnection),
                 lambda pkt: pkt.connection_type == 0x03 and pkt.structure_length > 0x02),
                (PacketField("connection_data", CRDTunnelingConnection(), CRDTunnelingConnection),
                 lambda pkt: pkt.connection_type == 0x04 and pkt.structure_length > 0x02)
            ],
            PacketField("connection_data", None, ByteField)
        )
    ]


# cEMI blocks

class LcEMI(Packet):
    name = "L_cEMI"
    fields_desc = [
        FieldLenField("additional_information_length", 0, fmt="B", length_of="additional_information"),
        StrLenField("additional_information", None, length_from=lambda pkt: pkt.additional_information_length),
        # Controlfield 1 (1 byte made of 8*1 bits)
        BitEnumField("frame_type", 1, 1, {
            1: "standard"
        }),
        BitField("reserved", 0, 1),
        BitField("repeat_on_error", 1, 1),
        BitEnumField("broadcast_type", 1, 1, {
            1: "domain"
        }),
        BitEnumField("priority", 3, 2, {
            3: "low"
        }),
        BitField("ack_request", 0, 1),
        BitField("confirmation_error", 0, 1),
        # Controlfield 2 (1 byte made of 1+3+4 bits)
        BitEnumField("address_type", 1, 1, {
            1: "group"
        }),
        BitField("hop_count", 6, 3),
        BitField("extended_frame_format", 0, 4),
        KNXAddressField("source_address", None),
        KNXGroupField("destination_address", "1/2/3"),
        FieldLenField("npdu_length", 0x01, fmt="B", length_of="data"),
        # TPCI and APCI (2 byte made of 1+1+4+4+6 bits)
        BitEnumField("packet_type", 0, 1, {
            0: "data"
        }),
        BitEnumField("sequence_type", 0, 1, {
            0: "unnumbered"
        }),
        BitField("reserved2", 0, 4),
        BitEnumField("acpi", 2, 4, {
            2: "GroupValueWrite"
        }),
        BitField("reserved3", 0, 6),
        StrLenField("data", None, length_from=lambda pkt: pkt.npdu_length) # to be tested

    ]


class DPcEMI(Packet):
    name = "DP_cEMI"
    fields_desc = [
        # see if best representation is str or hex
        ShortField("object_type", None),
        ByteField("object_instance", None),
        ByteField("property_id", None),
        BitField("number_of_elements", None, 4),
        BitField("start_index", None, 12)
    ]


class LDataReq(Packet):
    name = "L_Data.req"
    fields_desc = [
        PacketField("L_Data.req", LcEMI(), LcEMI)
    ]


class LDataCon(Packet):
    name = "L_Data.con"
    fields_desc = [
        PacketField("L_Data.con", LcEMI(), LcEMI)
    ]


class PropReadReq(Packet):
    name = "PropRead.req"
    fields_desc = [
        PacketField("PropRead.req", DPcEMI(), DPcEMI)
    ]


class PropReadCon(Packet):
    name = "PropRead.con"
    fields_desc = [
        PacketField("PropRead.con", DPcEMI(), DPcEMI)
    ]


class PropWriteReq(Packet):
    name = "PropWrite.req"
    fields_desc = [
        PacketField("PropWrite.req", DPcEMI(), DPcEMI)
    ]


class PropWriteCon(Packet):
    name = "PropWrite.con"
    fields_desc = [
        PacketField("PropWrite.con", DPcEMI(), DPcEMI)
    ]


class CEMI(Packet):
    name = "CEMI"
    fields_desc = [
        ByteEnumField("message_code", None, MESSAGE_CODES),
        MultipleTypeField(
            [
                (PacketField("cemi_data", LDataReq(), LDataReq), lambda pkt: pkt.message_code == 0x11),
                (PacketField("cemi_data", LDataCon(), LDataCon), lambda pkt: pkt.message_code == 0x2e),
                (PacketField("cemi_data", PropReadReq(), PropReadReq), lambda pkt: pkt.message_code == 0xFC),
                (PacketField("cemi_data", PropReadCon(), PropReadCon), lambda pkt: pkt.message_code == 0xFB),
                (PacketField("cemi_data", PropWriteReq(), PropWriteReq), lambda pkt: pkt.message_code == 0xF6),
                (PacketField("cemi_data", PropWriteCon(), PropWriteCon), lambda pkt: pkt.message_code == 0xF5)
            ],
            PacketField("cemi_data", None, ByteField)
        )
    ]


### KNX SERVICES

class KNXSearchRequest(Packet):
    name = "SEARCH_REQUEST",
    fields_desc = [
        PacketField("discovery_endpoint", HPAI(), HPAI)
    ]


class KNXSearchResponse(Packet):
    name = "SEARCH_RESPONSE",
    fields_desc = [
        PacketField("control_endpoint", HPAI(), HPAI),
        PacketField("device_info", DIBDeviceInfo(), DIBDeviceInfo),
        PacketField("supported_service_families", DIBSuppSvcFamilies(), DIBSuppSvcFamilies)
    ]


class KNXDescriptionRequest(Packet):
    name = "DESCRIPTION_REQUEST"
    fields_desc = [
        PacketField("control_endpoint", HPAI(), HPAI)
    ]


class KNXDescriptionResponse(Packet):
    name = "DESCRIPTION_RESPONSE"
    fields_desc = [
        PacketField("device_info", DIBDeviceInfo(), DIBDeviceInfo),
        PacketField("supported_service_families", DIBSuppSvcFamilies(), DIBSuppSvcFamilies)
        # TODO: this is an optional field in KNX specs, add conditions to take it into account
        # PacketField("other_device_info", DIBDeviceInfo(), DIBDeviceInfo)
    ]


class KNXConnectRequest(Packet):
    name = "CONNECT_REQUEST"
    fields_desc = [
        PacketField("control_endpoint", HPAI(), HPAI),
        PacketField("data_endpoint", HPAI(), HPAI),
        PacketField("connection_request_information", CRI(), CRI)
    ]


class KNXConnectResponse(Packet):
    name = "CONNECT_RESPONSE"
    fields_desc = [
        ByteField("communication_channel_id", None),
        ByteField("status", None),
        PacketField("data_endpoint", HPAI(), HPAI),
        PacketField("connection_response_data_block", CRD(), CRD)
    ]


class KNXConnectionstateRequest(Packet):
    name = "CONNECTIONSTATE_REQUEST"
    fields_desc = [
        ByteField("communication_channel_id", None),
        ByteField("reserved", None),
        PacketField("control_endpoint", HPAI(), HPAI)
    ]


class KNXConnectionstateResponse(Packet):
    name = "CONNECTIONSTATE_RESPONSE"
    fields_desc = [
        ByteField("communication_channel_id", None),
        ByteField("status", 0x00)
    ]


class KNXDisconnectRequest(Packet):
    name = "DISCONNECT_REQUEST"
    fields_desc = [
        ByteField("communication_channel_id", 0x01),
        ByteField("reserved", None),
        PacketField("control_endpoint", HPAI(), HPAI)
    ]


class KNXDisconnectResponse(Packet):
    name = "DISCONNECT_RESPONSE"
    fields_desc = [
        ByteField("communication_channel_id", None),
        ByteField("status", 0x00)
    ]


class KNXConfigurationRequest(Packet):
    name = "CONFIGURATION_REQUEST"
    fields_desc = [
        ByteField("structure_length", 0x04),
        ByteField("communication_channel_id", 0x01),
        ByteField("sequence_counter", None),
        ByteField("reserved", None),
        PacketField("cemi", CEMI(), CEMI)
    ]

    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay


class KNXConfigurationACK(Packet):
    name = "CONFIGURATION_ACK"
    fields_desc = [
        ByteField("structure_length", None),
        ByteField("communication_channel_id", 0x01),
        ByteField("sequence_counter", None),
        ByteField("status", None)
    ]

    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay


class KNXTunnelingRequest(Packet):
    name = "TUNNELING_REQUEST"
    fields_desc = [
        ByteField("structure_length", 0x04),
        ByteField("communication_channel_id", 0x01),
        ByteField("sequence_counter", None),
        ByteField("reserved", None),
        PacketField("cemi", CEMI(), CEMI)
    ]

    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay


class KNXTunnelingACK(Packet):
    name = "TUNNELING_ACK"
    fields_desc = [
        ByteField("structure_length", None),
        ByteField("communication_channel_id", 0x01),
        ByteField("sequence_counter", None),
        ByteField("status", None)
    ]

    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay


### KNX FRAME

class KNXHeader(Packet):
    name = "Header"
    fields_desc = [
        ByteField("header_length", None),
        XByteField("protocol_version", 0x10),
        ShortEnumField("service_identifier", None, SERVICE_IDENTIFIER_CODES),
        ShortField("total_length", None)
    ]
    def post_build(self, p, pay):
        p = (len(p)).to_bytes(1, byteorder='big') + p[1:]
        return p + pay
    # possible to do this with a dedicated field instead of a post_build ??


### LAYERS BINDING


bind_layers(KNXHeader, KNXSearchRequest, service_identifier=0x0201)
bind_layers(KNXHeader, KNXSearchResponse, service_identifier=0x0202)
bind_layers(KNXHeader, KNXDescriptionRequest, service_identifier=0x0203)
bind_layers(KNXHeader, KNXDescriptionResponse, service_identifier=0x0204)
bind_layers(KNXHeader, KNXConnectRequest, service_identifier=0x0205)
bind_layers(KNXHeader, KNXConnectResponse, service_identifier=0x0206)
bind_layers(KNXHeader, KNXConnectionstateRequest, service_identifier=0x0207)
bind_layers(KNXHeader, KNXConnectionstateResponse, service_identifier=0x0208)
bind_layers(KNXHeader, KNXDisconnectResponse, service_identifier=0x020A)
bind_layers(KNXHeader, KNXDisconnectRequest, service_identifier=0x0209)
bind_layers(KNXHeader, KNXConfigurationRequest, service_identifier=0x0310)
bind_layers(KNXHeader, KNXConfigurationACK, service_identifier=0x0311)
bind_layers(KNXHeader, KNXTunnelingRequest, service_identifier=0x0420)
bind_layers(KNXHeader, KNXTunnelingACK, service_identifier=0x0421)

# for now we bind every layer used as PacketField to Padding in order to delete its payload
# (solution inspired by https://github.com/secdev/scapy/issues/360)
# we could also define a new Packet class with no payload (or does it already exists as NoPayload ???)

bind_layers(HPAI, Padding)
bind_layers(ServiceFamily, Padding)
bind_layers(DIBDeviceInfo, Padding)
bind_layers(DIBSuppSvcFamilies, Padding)
bind_layers(DeviceManagementConnection, Padding)
bind_layers(TunnelingConnection, Padding)
bind_layers(CRDTunnelingConnection, Padding)
bind_layers(CRI, Padding)
bind_layers(CRD, Padding)
bind_layers(LcEMI, Padding)
bind_layers(DPcEMI, Padding)
bind_layers(LDataReq, Padding)
bind_layers(LDataCon, Padding)
bind_layers(PropReadReq, Padding)
bind_layers(PropReadCon, Padding)
bind_layers(PropWriteReq, Padding)
bind_layers(PropWriteCon, Padding)
bind_layers(CEMI, Padding)

bind_layers(KNXSearchRequest, Padding)
bind_layers(KNXSearchResponse, Padding)
bind_layers(KNXDescriptionRequest, Padding)
bind_layers(KNXDescriptionResponse, Padding)
bind_layers(KNXConnectRequest, Padding)
bind_layers(KNXConnectResponse, Padding)
bind_layers(KNXConnectionstateRequest, Padding)
bind_layers(KNXConnectionstateResponse, Padding)
bind_layers(KNXDisconnectRequest, Padding)
bind_layers(KNXDisconnectResponse, Padding)
bind_layers(KNXConfigurationRequest, Padding)
bind_layers(KNXConfigurationACK, Padding)
bind_layers(KNXTunnelingRequest, Padding)
bind_layers(KNXTunnelingACK, Padding)

bind_layers(KNXHeader, Padding)

# TODO: add ByteEnumField with status list (see KNX specifications)
# TODO: replace MultipleTypeField in CEMI with Scapy bindings
# TODO: compute length, see if could be done with dedicated field

