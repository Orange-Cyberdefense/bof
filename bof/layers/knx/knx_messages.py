"""
KNX messages
------------

Module containing a set of functions to build predefined types of KNX messages.
Functions in this module do not handle the network exchange, they just create
ready-to-send packets.

Contents:

:KNXnet/IP requests:
    Direct methods to create initialized requests from the standard.
:CEMI:
    Methods to create specific type of cEMI messages (protocol-independent
    KNX messages).
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
    """Creates a basic search request with appropriate source.

    :param knxnet: The KNXnet connection object to use. We only need the 
                   source parameter, please create an issue if you think that
                   asking directly for the source instead is a better choice.
    :returns: A search request as a KNXPacket.
    """
    search_req = KNXPacket(type=SID.search_request)
    if knxnet and isinstance(knxnet, KNXnet) and knxnet.is_connected:
        search_req.ip_address, search_req.port = knxnet.source
    return search_req

#-----------------------------------------------------------------------------#
# DESCRIPTION REQUEST (0x0203)                                                #
#-----------------------------------------------------------------------------#

def description_request(knxnet: KNXnet=None) -> KNXPacket:
    """Creates a basic description request with appropriate source.

    :param knxnet: The KNXnet connection object to use. We only need the 
                   source parameter, please create an issue if you think that
                   asking directly for the source instead is a better choice.
    :returns: A description request as a KNXPacket.
    """
    descr_req = KNXPacket(type=SID.description_request)
    if knxnet and isinstance(knxnet, KNXnet) and knxnet.is_connected:
        descr_req.ip_address, descr_req.port = knxnet.source
    return descr_req

#-----------------------------------------------------------------------------#
# CONNECT REQUEST (0x0205)                                                    #
#-----------------------------------------------------------------------------#

def connect_request_management(knxnet: KNXnet=None) -> KNXPacket:
    """Creates a connect request with device management connection type.

    :param knxnet: The KNXnet connection object to use. We only need the 
                   source parameter, please create an issue if you think that
                   asking directly for the source instead is a better choice.
    :returns: A management connect request as a KNXPacket.
    """
    conn_req = KNXPacket(type=SID.connect_request,
                         connection_type=CONNECTION_TYPE_CODES.device_management_connection)
    if knxnet and isinstance(knxnet, KNXnet) and knxnet.is_connected:
        conn_req.scapy_pkt.control_endpoint.ip_address = knxnet.source_address
        conn_req.scapy_pkt.control_endpoint.port = knxnet.source_port
        conn_req.scapy_pkt.data_endpoint.ip_address = knxnet.source_address
        conn_req.scapy_pkt.data_endpoint.port = knxnet.source_port
    return conn_req

def connect_request_tunneling(knxnet: KNXnet=None) -> KNXPacket:
    """Creates a connect request with tunneling connection type.

    :param knxnet: The KNXnet connection object to use. We only need the 
                   source parameter, please create an issue if you think that
                   asking directly for the source instead is a better choice.
    :returns: A tunneling connect request as a KNXPacket.
    """
    conn_req = KNXPacket(type=SID.connect_request,
                         connection_type=CONNECTION_TYPE_CODES.tunnel_connection)
    if knxnet and isinstance(knxnet, KNXnet) and knxnet.is_connected:
        conn_req.scapy_pkt.control_endpoint.ip_address = knxnet.source_address
        conn_req.scapy_pkt.control_endpoint.port = knxnet.source_port
        conn_req.scapy_pkt.data_endpoint.ip_address = knxnet.source_address
        conn_req.scapy_pkt.data_endpoint.port = knxnet.source_port
    return conn_req

#-----------------------------------------------------------------------------#
# DISCONNECT REQUEST (0x020A)                                                 #
#-----------------------------------------------------------------------------#

def disconnect_request(knxnet: KNXnet=None, channel: int=1) -> KNXPacket:
    """Creates a disconnect request to close connection on given channel.

    :param knxnet: The KNXnet connection object to use. We only need the 
                   source parameter, please create an issue if you think that
                   asking directly for the source instead is a better choice.
    :param channel: The communication channel ID for the current KNXnet/IP
                    connection. The channel is set by the server and returned
                    in connect responses.
    :returns: A disconnect request as a KNXPacket.
    """
    disco_req = KNXPacket(type=SID.disconnect_request)
    if knxnet and isinstance(knxnet, KNXnet) and knxnet.is_connected:
        disco_req.ip_address, disco_req.port = knxnet.source
    disco_req.communication_channel_id = channel
    return disco_req

#-----------------------------------------------------------------------------#
# CONFIGURATION REQUEST (0x0310)                                              #
#-----------------------------------------------------------------------------#

def configuration_request(channel: int, cemi: Packet) -> KNXPacket:
    """Creates a configuration request with a specified cEMI message.

    :param channel: The communication channel ID for the current KNXnet/IP
                    connection. The channel is set by the server and returned
                    in connect responses.
    :param cemi: Protocol-independent KNX message inserted in the request.
                 cEMI are created directly from Scapy's CEMI object.
    :returns: A configuration request embedding a cEMI packet, as a KNXPacket.
    """
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
    """Creates a tunneling request with a specified cEMI message.

    :param channel: The communication channel ID for the current KNXnet/IP
                    connection. The channel is set by the server and returned
                    in connect responses.
    :param sequence_counter: Sequence number to use for the request, same
                             principle as TCP's sequence numbers.
    :param cemi: Protocol-independent KNX message inserted in the request.
                 cEMI are created directly from Scapy's CEMI object.
    :returns: A tunneling request embedding a cEMI packet, as a KNXPacket.
    """
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
# M_PropRead.req (0x11) with ACPI GroupValueWrite                             #
#-----------------------------------------------------------------------------#

def cemi_property_read(object_type: int, property_id: int) -> Packet:
    """Builds a KNX message (cEMI) to write a value to a group address.

    :param object_type: Type of object to read, as defined in KNX Standard (and
                        reproduce in Scapy's KNX implementation).
    :param property_id: Property to read, as defined in KNX Standard (and
                        reproduce in Scapy's KNX implementation).
    :returns: A raw cEMI object from Scapy's implementation to be inserted in
              a KNXPacket object.
    """
    cemi = scapy_knx.CEMI(message_code=CEMI.m_propread_req)
    cemi.cemi_data.object_type = object_type
    cemi.cemi_data.property_id = property_id
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with ACPI GroupValueWrite                                 #
#-----------------------------------------------------------------------------#

def cemi_group_write(knx_group_addr: str, value, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to write a value to a group address.

    :param knx_group_addr: KNX group address targeted (with format X/Y/Z)
                           Group addresses are defined in KNX project settings.
    :param value: Value to set the group address' content to.
    :param knx_source: KNX individual address to use as a source for the
                       request. You should usually use the KNXnet/IP server's
                       individual address, but it works fine with 0.0.0.
    :returns: A raw cEMI object from Scapy's implementation to be inserted in
              a KNXPacket object.
    :raises BOFProgrammingError: if KNX addresses are invalid because the Scapy
                                 object does not allow that. You should change
                                 the field type if you want to set somethig else.
    """
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    try:
        cemi.cemi_data.source_address = knx_source
        cemi.cemi_data.destination_address = knx_group_addr
    except ValueError:
        raise BOFProgrammingError("Values given to addresses are not supported.")
    cemi.cemi_data.acpi = ACPI.groupvaluewrite
    cemi.cemi_data.data = int(value)
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with ACPI DevDescrRead                                    #
#-----------------------------------------------------------------------------#

def cemi_dev_descr_read(knx_indiv_addr: str, seq_num: int=0, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to write a value to a group address.

    :param knx_indiv_addr: KNX individual address of device (with format X.Y.Z)
    :param seq_num: Sequence number to use, applies to cEMI when sequence_type
                    is set to "numbered". So far I haven't seen seq_num > 0.
    :param knx_source: KNX individual address to use as a source for the
                       request. You should usually use the KNXnet/IP server's
                       individual address, but it works fine with 0.0.0.
    :returns: A raw cEMI object from Scapy's implementation to be inserted in
              a KNXPacket object.
    :raises BOFProgrammingError: if KNX addresses are invalid because the Scapy
                                 object does not allow that. You should change
                                 the field type if you want to set somethig else.
    """
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    try:
        cemi.cemi_data.source_address = knx_source
        cemi.cemi_data.destination_address = knx_indiv_addr
    except ValueError:
        raise BOFProgrammingError("Values given to addresses are not supported.")
    cemi.cemi_data.npdu_length = 1 # size of data
    cemi.cemi_data.packet_type = 0 # data
    cemi.cemi_data.sequence_type = 1 # numbered
    cemi.cemi_data.sequence_number = seq_num
    cemi.cemi_data.acpi = ACPI.devdescrread
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with type Control, service Connect                        #
#-----------------------------------------------------------------------------#

def cemi_connect(knx_indiv_addr: str, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to connect to an individual address.

    :param knx_indiv_addr: KNX individual address of device (with format X.Y.Z)
    :param knx_source: KNX individual address to use as a source for the
                       request. You should usually use the KNXnet/IP server's
                       individual address, but it works fine with 0.0.0.
    :returns: A raw cEMI object from Scapy's implementation to be inserted in
              a KNXPacket object.
    :raises BOFProgrammingError: if KNX addresses are invalid because the Scapy
                                 object does not allow that. You should change
                                 the field type if you want to set somethig else.
    """
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    try:
        cemi.cemi_data.source_address = knx_source
        cemi.cemi_data.destination_address = knx_indiv_addr
    except ValueError:
        raise BOFProgrammingError("Values given to addresses are not supported.")
    cemi.cemi_data.npdu_length = 0 # no data
    cemi.cemi_data.packet_type = 1 # control
    cemi.cemi_data.sequence_type = 0 # unnumbered
    cemi.cemi_data.service = 0 # connect
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with type Control, service Disconnect                     #
#-----------------------------------------------------------------------------#

def cemi_disconnect(knx_indiv_addr: str, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to disconnect from an individual address.

    :param knx_indiv_addr: KNX individual address of device (with format X.Y.Z)
    :param knx_source: KNX individual address to use as a source for the
                       request. You should usually use the KNXnet/IP server's
                       individual address, but it works fine with 0.0.0.
    :returns: A raw cEMI object from Scapy's implementation to be inserted in
              a KNXPacket object.
    :raises BOFProgrammingError: if KNX addresses are invalid because the Scapy
                                 object does not allow that. You should change
                                 the field type if you want to set somethig else.
    """
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    try:
        cemi.cemi_data.source_address = knx_source
        cemi.cemi_data.destination_address = knx_indiv_addr
    except ValueError:
        raise BOFProgrammingError("Values given to addresses are not supported.")
    cemi.cemi_data.npdu_length = 0 # no data
    cemi.cemi_data.packet_type = 1 # control
    cemi.cemi_data.sequence_type = 0 # unnumbered
    cemi.cemi_data.service = 1 # disconnect
    return cemi

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with type Control, service ACK                            #
#-----------------------------------------------------------------------------#

def cemi_ack(knx_indiv_addr: str, seq_num: int=0, knx_source: str="0.0.0") -> Packet:
    """Builds a KNX message (cEMI) to disconnect from an individual address.

    :param knx_indiv_addr: KNX individual address of device (with format X.Y.Z)
    :param seq_num: Sequence number to use, applies to cEMI when sequence_type
                    is set to "numbered". So far I haven't seen seq_num > 0.
    :param knx_source: KNX individual address to use as a source for the
                       request. You should usually use the KNXnet/IP server's
                       individual address, but it works fine with 0.0.0.
    :returns: A raw cEMI object from Scapy's implementation to be inserted in
              a KNXPacket object.
    :raises BOFProgrammingError: if KNX addresses are invalid because the Scapy
                                 object does not allow that. You should change
                                 the field type if you want to set somethig else.
    """
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.priority = 0 # system
    cemi.cemi_data.address_type = 0 # individual
    try:
        cemi.cemi_data.source_address = knx_source
        cemi.cemi_data.destination_address = knx_indiv_addr
    except ValueError:
        raise BOFProgrammingError("Values given to addresses are not supported.")
    cemi.cemi_data.npdu_length = 0 # no data
    cemi.cemi_data.packet_type = 1 # control
    cemi.cemi_data.sequence_type = 1 # numbered
    cemi.cemi_data.sequence_number = seq_num
    cemi.cemi_data.service = 2 # ack
    return cemi
