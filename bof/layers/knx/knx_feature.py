"""
KNX features
------------

This module contains a set of higher-level functions to interact with devices
using KNXnet/IP without prior knowledge about the protocol.

Contents:

:KNXDevice:
    An object representation of a KNX device with multiple properties. Only
    supports KNXnet/IP servers so far, but will be extended to KNX devices.
:Features:
    High-level functions to interact with a device: search, discover, read,
    write, etc.
:KNXnet/IP requests:
    Direct methods to send initialized requests from the standard.
:CEMI:
    Methods to create specific type of cEMI messages (protocol-independent
    KNX messages.
"""

from ipaddress import ip_address
# Internal
from ... import BOFNetworkError, BOFProgrammingError
from .knx_network import *
from .knx_packet import *
from ...layers.raw_scapy import knx as scapy_knx 

###############################################################################
# CONSTANTS                                                                   #
###############################################################################

MULTICAST_ADDR = "224.0.23.12"
KNX_PORT = 3671

CONNECTION_TYPE_CODES = type('CONNECTION_TYPE_CODES', (object,),
                             {to_property(v):k for k,v in scapy_knx.CONNECTION_TYPE_CODES.items()})()

CEMI_OBJECT_TYPES = type('CEMI_OBJECT_TYPES', (object,),
                         {to_property(v):k for k,v in scapy_knx.CEMI_OBJECT_TYPES.items()})()

CEMI_PROPERTIES = type('CEMI_PROPERTIES', (object,),
                       {to_property(v):k for k,v in scapy_knx.CEMI_PROPERTIES.items()})()

def IS_IP(ip: str):
    """Check that ip is a recognized IPv4 address."""
    try:
        ip_address(ip)
    except ValueError:
        raise BOFProgrammingError("Invalid IP {0}".format(ip)) from None


###############################################################################
# KNX DEVICE REPRESENTATION                                                   #
###############################################################################

class KNXDevice(object):
    """Object representing a KNX device.

    Information contained in the object are the one returned by SEARCH
    RESPONSE and DESCRIPTION RESPONSE messages.
    May be completed, improved later.
    """
    def __init__(self, name: str, ip_address: str, port: int, knx_address: str,
                 mac_address: str, multicast_address: str=MULTICAST_ADDR,
                 serial_number: str=""):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.knx_address = knx_address
        self.mac_address = mac_address
        self.multicast_address = multicast_address
        self.serial_number = serial_number

    def __str__(self):
        descr = ["Device: \"{0}\" @ {1}:{2}".format(self.name,
                                                    self.ip_address,
                                                    self.port)]
        descr += ["- KNX address: {0}".format(self.knx_address)]
        descr += ["- Hardware: {0} (SN: {1})".format(self.mac_address,
                                                     self.serial_number)]
        return " ".join(descr)

    @classmethod
    def init_from_search_response(cls, response: KNXPacket):
        """Set appropriate values according to the content of search response.

        :param response: Search Response provided by a device as a KNXPacket.
        :returns: A KNXDevice object.
        """
        args = {
            "name": response.device_friendly_name.decode('utf-8'),
            "ip_address": response.ip_address,
            "port": response.port,
            "knx_address": scapy_knx.KNXAddressField.i2repr(None, None, response.knx_address),
            "mac_address": response.device_mac_address,
            "multicast_address": response.device_multicast_address,
            "serial_number": response.device_serial_number
        }
        return cls(**args)

    @classmethod
    def init_from_description_response(cls, response: KNXPacket, source: tuple):
        """Set appropriate values according to the content of description response.

        :param response: Description Response provided by a device as a KNXPacket.
        :returns: A KNXDevice object.
        """
        args = {
            "name": response.device_friendly_name.decode('utf-8'),
            "ip_address": source[0],
            "port": source[1],
            "knx_address": scapy_knx.KNXAddressField.i2repr(None, None, response.knx_address),
            "mac_address": response.device_mac_address,
            "multicast_address": response.device_multicast_address,
            "serial_number": response.device_serial_number            
        }
        return cls(**args)

###############################################################################
# FEATURES                                                                    #
###############################################################################

#-----------------------------------------------------------------------------#
# Discovery                                                                   #
#-----------------------------------------------------------------------------#

def search(ip: object=MULTICAST_ADDR, port: int=KNX_PORT) -> list:
    """Search for KNX devices on an network (multicast, unicast address(es).
    Sends a SEARCH REQUEST per IP and expects one SEARCH RESPONSE per device.
    **KNX Standard v2.1**

    :param ip: Multicast, unicast IPv4 address or list of such addresses to
               search for.  Default value is default KNXnet/IP multicast
               address 224.0.23.12.
    :param port: KNX port, default is 3671.
    :returns: The list of responding KNXnet/IP devices in the network as
              KNXDevice objects.
    :raises BOFProgrammingError: if IP is invalid.
    """
    devices = []
    if isinstance(ip, str):
        ip = [ip]
    for i in ip:
        IS_IP(i)
        knxnet = KNXnet().connect(i, port)
        search_req = KNXPacket(type=SID.search_request)
        search_req.ip_address, search_req.port = knxnet.source
        try:
            knxnet.send(search_req)
            while 1:
                response, _ = knxnet.receive()
                devices.append(KNXDevice.init_from_search_response(response))
        except BOFNetworkError:
            pass
        knxnet.disconnect()
    return devices

def discover(ip: str, port: int=KNX_PORT) -> KNXDevice:
    """Returns discovered information about a device.
    SO far, only sends a DESCRIPTION REQUEST and uses the DESCRIPTION RESPONSE.
    This function may evolve to include all underlying devices.

    :param ip: IPv4 address of KNX device.
    :param port: KNX port, default is 3671.
    :returns: A KNXDevice object.
    :raises BOFProgrammingError: if IP is invalid.
    :raises BOFNetworkError: if device cannot be reached.
    """
    IS_IP(ip)
    knxnet = KNXnet().connect(ip, port)
    channel = connect_request_management(knxnet)
    response, source = description_request(knxnet)
    device = KNXDevice.init_from_description_response(response, source)
    # cemi = cemi_property_read(CEMI_OBJECT_TYPES.ip_parameter_object,
    #                           CEMI_PROPERTIES.pid_additional_individual_addresses)
    # response = configuration_request(knxnet, channel, cemi)
    disconnect_request(knxnet, channel)
    knxnet.disconnect()
    return device

#-----------------------------------------------------------------------------#
# Read and write operations                                                   #
#-----------------------------------------------------------------------------#

def group_write(ip: str, knx_group_addr: str, value, port: int=3671) -> KNXPacket:
    """Writes value to KNX group address via the server at address ip.
    We first need to establish a tunneling connection so that we can reach
    underlying device groups.
    """
    IS_IP(ip)
    knxnet = KNXnet().connect(ip, port)
    # Start tunneling connection
    channel, knx_source = connect_request_tunneling(knxnet)
    cemi = cemi_group_write(knx_source, knx_group_addr, value)
    response, _ = tunneling_request(knxnet, channel, cemi)
    # End tunneling connection
    disconnect_request(knxnet, channel)
    knxnet.disconnect()
    return response

###############################################################################
# KNXnet/IP REQUESTS                                                          #
###############################################################################

#-----------------------------------------------------------------------------#
# SEARCH REQUEST (0x0201)                                                     #
#-----------------------------------------------------------------------------#

def search_request(knxnet: KNXnet) -> KNXPacket:
    """Sends a basic search request with appropriate source."""
    search_req = KNXPacket(type=SID.search_request)
    search_req.ip_address, search_req.port = knxnet.source
    response, source = knxnet.sr(search_req)
    return response, source

#-----------------------------------------------------------------------------#
# DESCRIPTION REQUEST (0x0203)                                                #
#-----------------------------------------------------------------------------#

def description_request(knxnet: KNXnet) -> (KNXPacket, tuple):
    """Sends a basic description request with appropriate source."""
    descr_req = KNXPacket(type=SID.description_request)
    descr_req.ip_address, descr_req.port = knxnet.source
    response, source = knxnet.sr(descr_req)
    return response, source

#-----------------------------------------------------------------------------#
# CONNECT REQUEST (0x0205)                                                    #
#-----------------------------------------------------------------------------#

def connect_request_management(knxnet: KNXnet) -> int:
    """Connect to a device with device management connection mode.
    Sends a CONNECT REQUEST with device management connection type.
    We want to retrieve the "channel" field, which will be used during the 
    device management exchange.
    """
    conn_req = KNXPacket(type=SID.connect_request,
                         connection_type=CONNECTION_TYPE_CODES.device_management_connection)
    conn_req.scapy_pkt.control_endpoint.ip_address, conn_req.scapy_pkt.control_endpoint.port = knxnet.source
    conn_req.scapy_pkt.data_endpoint.ip_address, conn_req.scapy_pkt.data_endpoint.port = knxnet.source
    response, _ = knxnet.sr(conn_req)
    return response.communication_channel_id

def connect_request_tunneling(knxnet: KNXnet) -> (int, str):
    """Connect to a device with tunneling connection mode.
    Sends a CONNECT REQUEST with tunneling connection type.
    We want to retrieve the "channel" and source "KNX individual address"
    fields, which will be used during the tunneling exchange.
    """
    conn_req = KNXPacket(type=SID.connect_request,
                         connection_type=CONNECTION_TYPE_CODES.tunnel_connection)
    conn_req.scapy_pkt.control_endpoint.ip_address, conn_req.scapy_pkt.control_endpoint.port = knxnet.source
    conn_req.scapy_pkt.data_endpoint.ip_address, conn_req.scapy_pkt.data_endpoint.port = knxnet.source
    response, _ = knxnet.sr(conn_req)
    knx_source = response.scapy_pkt.connection_response_data_block.connection_data.knx_individual_address
    channel_id = response.scapy_pkt.communication_channel_id
    return channel_id, knx_source

#-----------------------------------------------------------------------------#
# DISCONNECT REQUEST (0x020A)                                                 #
#-----------------------------------------------------------------------------#

def disconnect_request(knxnet: KNXnet, channel: int) -> None:
    """Sends a disconnect request to close initiated connection on channel."""
    disco_req = KNXPacket(type=SID.disconnect_request)
    disco_req.ip_address, disco_req.port = knxnet.source
    disco_req.communication_channel_id = channel
    response, _ = knxnet.sr(disco_req)

#-----------------------------------------------------------------------------#
# CONFIGURATION REQUEST (0x0310)                                              #
#-----------------------------------------------------------------------------#

def configuration_request(knxnet: KNXnet, channel: int, cemi: Packet) -> (KNXPacket, tuple):
    """Sends a configuration request with a specified cEMI message.
    The server first replies with an ach, then the response (or at least we
    home it will arrive in the order x)).
    We need to ack back after receiving the response.
    """
    config_req = KNXPacket(type=SID.configuration_request)
    config_req.communication_channel_id = channel
    config_req.cemi = cemi
    ack, _ = knxnet.sr(config_req)
    response, source = knxnet.receive()
    # We have to ACK when we receive tunneling requests
    if response.sid == SID.configuration_request and \
       response.message_code == CEMI.m_propread_con:
        ack = KNXPacket(type=SID.configuration_ack, communication_channel_id=channel)
        knxnet.send(ack)
    return response, source

#-----------------------------------------------------------------------------#
# TUNNELING REQUEST (0x0420)                                                  #
#-----------------------------------------------------------------------------#

def tunneling_request(knxnet: KNXnet, channel: int, cemi: Packet) -> (KNXPacket, tuple):
    """Sends a tunneling request with a specified cEMI message.
    The server first replies with an ack, then the response (or at least we 
    hope it will arrive in this order x)).
    We need to ack back after receiving the response.
    """
    tun_req = KNXPacket(type=SID.tunneling_request)
    tun_req.communication_channel_id = channel
    tun_req.cemi = cemi
    ack, _ = knxnet.sr(tun_req)
    response, source = knxnet.receive()
    # We have to ACK when we receive tunneling requests
    if response.sid == SID.tunneling_request and \
       response.message_code == CEMI.l_data_con:
        ack = KNXPacket(type=SID.tunneling_ack, communication_channel_id=channel)
        knxnet.send(ack)
    return response, source

###############################################################################
# KNX FIELD MESSAGES (cEMI)                                                   #
###############################################################################

#-----------------------------------------------------------------------------#
# L_data.req (0x11) with ACPI GroupValueWrite                                 #
#-----------------------------------------------------------------------------#

def cemi_group_write(knx_source: str, knx_group_addr: str, value) -> Packet:
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

def cemi_property_read(object_type: int, property_id: int) -> Packet:
    """Builds a KNX message (cEMI) to write a value to a group address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.m_propread_req)
    cemi.cemi_data.object_type = object_type
    cemi.cemi_data.property_id = property_id
    return cemi

