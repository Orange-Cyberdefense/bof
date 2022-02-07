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
    cemi = cemi_group_write(knx_group_addr, value, knx_source_address)
    ack, source = knxnet.sr(tunneling_request(channel, 0, cemi))
    response, source = knxnet.receive()
    knxnet.send(tunneling_ack(channel, 0))
    # End tunneling connection
    response, source = knxnet.sr(disconnect_request(knxnet, channel))
    knxnet.disconnect()
    return response

def individual_address_scan(ip: str, address: str="1.1.1", port: str=3671) -> bool:
    """Scans KNX gateway to find if individual address exists.
    We first need to establish a tunneling connection and use cemi connect
    messages on each address to find out which one responds.
    As the gateway will answer positively for each address (L_data.con), we
    also wait for L_data.ind which seems to indicate existing addresses.

    The ******* exchange required is (all this full udp obviously):
    01. -> tunnel connect request
    02. <- tunnel connect response
    03. -> tunnel req l_data.req connect
    04. <- tunnel ack
    05. <- tunnel req l_data.con connect
    06. -> tunnel ack
    07. -> tunnel req l_data.req dev descr req
    08. <- tunnel ack
    09. <- tunnel req l_data.con dev descr req
    10. -> tunnel ack
    11. <- tunnel req l_data.ind ack
    12. -> tunnel ack
    13. <- tunnel req l_data.ind dev descr resp
    14. -> tunnel ack
    15. -> tunnel req l_data.req ack
    16. <- tunnel ack
    17. <- tunnel req l_data.con ack
    18. -> tunnel ack
    19. -> tunnel req l_data.req disconnect
    20. <- tunnel ack
    21. <- tunnel req _ldata.con disconnect
    22. -> tunnel ack
    23. -> disconnect request
    24. <- disconnect response
    When device does not exists, frames 11 > 18 are replaced with whatever,
    I just don't get it.
    """
    IS_IP(ip)
    knxnet = KNXnet().connect(ip, port)
    # Start tunneling connection
    response, source = knxnet.sr(connect_request_tunneling(knxnet))
    channel = response.communication_channel_id
    # Send cemi connect request, wait for ack and response, ack back
    cemi = cemi_connect(address)
    ack, source = knxnet.sr(tunneling_request(channel, 0, cemi))
    response, source = knxnet.receive()
    knxnet.send(tunneling_ack(channel, 0))

    # Sends cemi device description read, wait for ack and response
    cemi = cemi_dev_descr_read(address)
    ack, source = knxnet.sr(tunneling_request(channel, 1, cemi))
    response, source = knxnet.receive() # dev descr resp
    knxnet.send(tunneling_ack(channel, response.sequence_counter))
    try:
        # If device exists, we should get a cemi ACK, to which we ack
        # Else, timeout (BOFNetworkError) is raised
        response, source = knxnet.receive()
        knxnet.send(tunneling_ack(channel, response.sequence_counter))
        # And then we get the answer we want which is a devdescrresp, and we ack
        response, source = knxnet.receive()
        knxnet.send(tunneling_ack(channel, response.sequence_counter))
        # And then we send a cemi ACK because why not and then we get an ack
        # and then a cemi ack to which we ack ffs
        cemi = cemi_ack(address)
        ack, source = knxnet.sr(tunneling_request(channel, 2, cemi))
        response, source = knxnet.receive()
        knxnet.send(tunneling_ack(channel, 4))
        # Send cemi disconnect request, wait for ack and response, ack back
        cemi = cemi_disconnect(address)
        ack, source = knxnet.sr(tunneling_request(channel, 3, cemi))
        response, source = knxnet.receive()
        knxnet.send(tunneling_ack(channel, 5))
        # End tunneling connection
        response, source = knxnet.sr(disconnect_request(knxnet, channel))
        exists = True
    except BOFNetworkError:
        exists = False
    finally:
        # We should send disconnect cemi and tunneling here but it times
        # out, i don't know why. now it works but the boiboite hates it
        # this should be changed and refactored because wtf knx seriously
        knxnet.disconnect()
    return exists
    
def line_scan(ip: str, line: str="1.1.0", port: int=3671) -> list:
    """Scans KNX gateway to find existing individual addresses on a line.
    We first need to establish a tunneling connection and use cemi connect
    messages on each address to find out which one responds.
    As the gateway will answer positively for each address (L_data.con), we
    also wait for L_data.ind which seems to indicate existing addresses.
    """
    # TODO: we need to re-implement and not call indiv_addr_scan
    # because it makes no sense to open a tunneling connection everytime.
    raise NotImplementedError("line_scan")
