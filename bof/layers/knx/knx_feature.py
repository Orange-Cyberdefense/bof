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
from .knx_messages import *
from ...layers.raw_scapy import knx as scapy_knx 

###############################################################################
# CONSTANTS                                                                   #
###############################################################################

MULTICAST_ADDR = "224.0.23.12"
KNX_PORT = 3671

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
        try:
            args = {
                "name": response.device_friendly_name.decode('utf-8'),
                "ip_address": response.ip_address,
                "port": response.port,
                "knx_address": scapy_knx.KNXAddressField.i2repr(None, None, response.knx_address),
                "mac_address": response.device_mac_address,
                "multicast_address": response.device_multicast_address,
                "serial_number": response.device_serial_number
            }
        except AttributeError:
            raise BOFNetworkError("Search Response has invalid format.") from None
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
    """Search for KNX devices on an network using multicast.
    Sends a SEARCH REQUEST and expects one SEARCH RESPONSE per device.
    **KNX Standard v2.1**

    :param ip: Multicast IPv4 address. Default value is default KNXnet/IP
               multicast address 224.0.23.12.
    :param port: KNX port, default is 3671.
    :returns: The list of responding KNXnet/IP devices in the network as
              KNXDevice objects.
    :raises BOFProgrammingError: if IP is invalid.
    """
    IS_IP(ip)
    devices = []
    responses = KNXnet.multicast(search_request(), (ip, port))
    for response, source in responses:
        device = KNXDevice.init_from_search_response(KNXPacket(response))
        devices.append(device)
    return devices

def discover(ip: str, port: int=KNX_PORT) -> KNXDevice:
    """Returns discovered information about a device.
    SO far, only sends a DESCRIPTION REQUEST and uses the DESCRIPTION RESPONSE.
    This function may evolve to gather data on underlying devices.

    :param ip: IPv4 address of KNX device.
    :param port: KNX port, default is 3671.
    :returns: A KNXDevice object.
    :raises BOFProgrammingError: if IP is invalid.
    :raises BOFNetworkError: if device cannot be reached.
    """
    IS_IP(ip)
    knxnet = KNXnet().connect(ip, port)
    # Initiate session
    response, source = knxnet.sr(connect_request_management(knxnet))
    channel = response.communication_channel_id
    # Information gathering
    response, source = knxnet.sr(description_request(knxnet))
    device = KNXDevice.init_from_description_response(response, source)
    # End session
    response, source = knxnet.sr(disconnect_request(knxnet, channel))
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
    response, source = knxnet.sr(connect_request_tunneling(knxnet))
    try:
        # TODO: why no direct access?
        response_data_block = response.scapy_pkt.connection_response_data_block
        knx_source_address = response_data_block.connection_data.knx_individual_address
        channel = response.scapy_pkt.communication_channel_id
    except AttributeError:
        raise BOFNetworkError("Cannot extract required data from response.") from None
    # Send group write request, wait for ack and response, ack back
    cemi = cemi_group_write(knx_source_address, knx_group_addr, value)
    ack, source = knxnet.sr(tunneling_request(channel, 0, cemi))
    response, source = knxnet.receive()
    knxnet.send(tunneling_ack(channel, 0))
    # End tunneling connection
    response, source = knxnet.sr(disconnect_request(knxnet, channel))
    knxnet.disconnect()
    return response
