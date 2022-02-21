"""
KNX messages
------------

Module containing a set of functions to build predefined types of KNX messages.
Functions in this module do not handle the network exchange, they just create
ready-to-send packets.
"""

from .knx_network import KNXnet
from .knx_packet import *
from ...layers.raw_scapy import knx as scapy_knx 

###############################################################################
# REQUESTS                                                                    #
###############################################################################

#-----------------------------------------------------------------------------#
# SEARCH REQUEST (0x0201)                                                     #
#-----------------------------------------------------------------------------#

def search_request(knxnet: KNXnet=None) -> KNXPacket:
    """Creates a basic search request with appropriate source."""
    search_req = KNXPacket(type=SID.search_request)
    if knxnet:
        search_req.ip_address, search_req.port = knxnet.source
    return search_req

#-----------------------------------------------------------------------------#
# DESCRIPTION REQUEST (0x0203)                                                #
#-----------------------------------------------------------------------------#

def description_request(knxnet: KNXnet=None) -> KNXPacket:
    """Creates a basic description request with appropriate source."""
    descr_req = KNXPacket(type=SID.description_request)
    if knxnet:
        descr_req.ip_address, descr_req.port = knxnet.source
    return descr_req

#-----------------------------------------------------------------------------#
# CONNECT REQUEST (0x0205)                                                    #
#-----------------------------------------------------------------------------#

def connect_request_management(knxnet: KNXnet) -> KNXPacket:
    """Creates a connect reqeuest with device management connection type."""
    conn_req = KNXPacket(type=SID.connect_request,
                         connection_type=CONNECTION_TYPE_CODES.device_management_connection)
    conn_req.scapy_pkt.control_endpoint.ip_address = knxnet.source_address
    conn_req.scapy_pkt.control_endpoint.port = knxnet.source_port
    conn_req.scapy_pkt.data_endpoint.ip_address = knxnet.source_address
    conn_req.scapy_pkt.data_endpoint.port = knxnet.source_port
    return conn_req

def connect_request_tunneling(knxnet: KNXnet) -> KNXPacket:
    """Creates a connect request with tunneling connection type."""
    conn_req = KNXPacket(type=SID.connect_request,
                         connection_type=CONNECTION_TYPE_CODES.tunnel_connection)
    conn_req.scapy_pkt.control_endpoint.ip_address = knxnet.source_address
    conn_req.scapy_pkt.control_endpoint.port = knxnet.source_port
    conn_req.scapy_pkt.data_endpoint.ip_address = knxnet.source_address
    conn_req.scapy_pkt.data_endpoint.port = knxnet.source_port
    return conn_req

#-----------------------------------------------------------------------------#
# DISCONNECT REQUEST (0x020A)                                                 #
#-----------------------------------------------------------------------------#

def disconnect_request(knxnet: KNXnet, channel: int) -> KNXPacket:
    """creates a disconnect request to close connection on given channel."""
    disco_req = KNXPacket(type=SID.disconnect_request)
    disco_req.ip_address, disco_req.port = knxnet.source
    disco_req.communication_channel_id = channel
    return disco_req

#-----------------------------------------------------------------------------#
# CONFIGURATION REQUEST (0x0310)                                              #
#-----------------------------------------------------------------------------#

def configuration_request(channel: int, cemi: Packet) -> KNXPacket:
    """Creates a configuration request with a specified cEMI message."""
    config_req = KNXPacket(type=SID.configuration_request)
    config_req.communication_channel_id = channel
    config_req.cemi = cemi
    return config_req

def configuration_ack(channel: int) -> KNXPacket:
    """Creates a configuration ack to reply to avoid upsetting KNX servers."""
    ack = KNXPacket(type=SID.configuration_ack)
    ack.communication_channel_id=channel
    return ack

#-----------------------------------------------------------------------------#
# TUNNELING REQUEST (0x0420)                                                  #
#-----------------------------------------------------------------------------#

def tunneling_request(channel: int, sequence_counter: int, cemi: Packet) -> KNXPacket:
    """Creates a tunneling request with a specified cEMI message."""
    tun_req = KNXPacket(type=SID.tunneling_request)
    tun_req.communication_channel_id = channel
    tun_req.sequence_counter = sequence_counter
    tun_req.cemi = cemi
    return tun_req

def tunneling_ack(channel: int, sequence_counter:int) -> KNXPacket:
    """Creates a tunneling ack to reply to avoid upsetting KNX servers."""
    ack = KNXPacket(type=SID.tunneling_ack)
    ack.communication_channel_id=channel
    ack.sequence_counter = sequence_counter
    return ack

###############################################################################
# KNX FIELD MESSAGES (cEMI)                                                   #
###############################################################################

#-----------------------------------------------------------------------------#
# M_PropRead.req (0x11) with ACPI GroupValueWrite                                 #
#-----------------------------------------------------------------------------#

def cemi_property_read(object_type: int, property_id: int) -> Packet:
    """Builds a KNX message (cEMI) to write a value to a group address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.m_propread_req)
    cemi.cemi_data.object_type = object_type
    cemi.cemi_data.property_id = property_id
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with ACPI GroupValueWrite                                 #
#-----------------------------------------------------------------------------#

def cemi_group_write(knx_group_addr: str, value, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to write a value to a group address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.source_address = knx_source
    cemi.cemi_data.destination_address = knx_group_addr
    cemi.cemi_data.acpi = ACPI.groupvaluewrite
    cemi.cemi_data.data = int(value)
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with ACPI GroupValueWrite                                 #
#-----------------------------------------------------------------------------#

def cemi_dev_descr_read(knx_indiv_addr: str, seq_num: int=0, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to write a value to a group address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    cemi.cemi_data.source_address = knx_source
    cemi.cemi_data.destination_address = knx_indiv_addr
    cemi.cemi_data.npdu_length = 1 # size of data
    cemi.cemi_data.packet_type = 0 # data
    cemi.cemi_data.sequence_type = 1 # numbered
    cemi.cemi_data.sequence_number = seq_num
    cemi.cemi_data.acpi = ACPI.devdescrread
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with type Control, service Connect                        #
#-----------------------------------------------------------------------------#

def cemi_connect(address: str, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to connect to an individual address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    cemi.cemi_data.destination_address = address
    cemi.cemi_data.npdu_length = 0 # no data
    cemi.cemi_data.packet_type = 1 # control
    cemi.cemi_data.sequence_type = 0 # unnumbered
    cemi.cemi_data.service = 0 # connect
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with type Control, service Disconnect                     #
#-----------------------------------------------------------------------------#

def cemi_disconnect(address: str, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to disconnect from an individual address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    cemi.cemi_data.destination_address = address
    cemi.cemi_data.npdu_length = 0 # no data
    cemi.cemi_data.packet_type = 1 # control
    cemi.cemi_data.sequence_type = 0 # unnumbered
    cemi.cemi_data.service = 1 # disconnect
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with type Control, service ACK                            #
#-----------------------------------------------------------------------------#

def cemi_ack(address: str, seq_num: int=0, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to disconnect from an individual address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    cemi.cemi_data.destination_address = address
    cemi.cemi_data.npdu_length = 0 # no data
    cemi.cemi_data.packet_type = 1 # control
    cemi.cemi_data.sequence_type = 1 # numbered
    cemi.cemi_data.sequence_number = seq_num
    cemi.cemi_data.service = 2 # ack
    return cemi
