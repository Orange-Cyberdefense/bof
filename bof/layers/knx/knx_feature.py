"""
KNX features
------------

This module contains a set of higher-level functions to interact with devices
using KNXnet/IP without prior knowledge about the protocol.

TODO
"""

from ipaddress import ip_address
# Internal
from ... import BOFNetworkError, BOFProgrammingError
from .knx_network import *
from .knx_packet import *
from ...layers.raw_scapy.knx import KNXAddressField

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
# DISCOVERY                                                                   #
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
            "knx_address": KNXAddressField.i2repr(None, None, response.knx_address),
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
            "knx_address": KNXAddressField.i2repr(None, None, response.knx_address),
            "mac_address": response.device_mac_address,
            "multicast_address": response.device_multicast_address,
            "serial_number": response.device_serial_number            
        }
        return cls(**args)

###############################################################################
# DISCOVERY                                                                   #
###############################################################################

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
    descr_req = KNXPacket(type=SID.description_request)
    descr_req.ip_address, descr_req.port = knxnet.source
    response, source = knxnet.sr(descr_req)
    knxnet.disconnect()
    return KNXDevice.init_from_description_response(response, source)

###############################################################################
# CONNECT / DISCONNECT                                                        #
###############################################################################

def connect_tunneling(ip: str, port: int=KNX_PORT) -> (KNXnet, int, str):
    """Connect to a device with tunneling connection mode.
    Sends a CONNECT REQUEST with tunneling connection type.
    We want to retrieve the "channel" and source "KNX individual address"
    fields, which will be used during the tunneling exchange.
    """
    IS_IP(ip)
    knxnet = KNXnet().connect(ip, port)
    conn_req = KNXPacket(type=SID.connect_request, connection_type=0x04)
    conn_req.scapy_pkt.control_endpoint.ip_address, conn_req.scapy_pkt.control_endpoint.port = knxnet.source
    conn_req.scapy_pkt.data_endpoint.ip_address, conn_req.scapy_pkt.data_endpoint.port = knxnet.source
    response, _ = knxnet.sr(conn_req)
    # FIX: we can't access knx_individual_address directly
    knx_source = response.scapy_pkt.connection_response_data_block.connection_data.knx_individual_address
    return knxnet, response.communication_channel_id, knx_source

def disconnect_tunneling(knxnet: KNXnet, channel: int) -> None:
    """Closes an initiated tunneling connection on channel.
    Sends a DISCONNECT REQUEST.
    """
    disco_req = KNXPacket(type=SID.disconnect_request)
    disco_req.ip_address, disco_req.port = knxnet.source
    disco_req.communication_channel_id = channel
    response, _ = knxnet.sr(disco_req)

###############################################################################
# KNX FIELD MESSAGES (cEMI)                                                   #
###############################################################################

def cemi_group_write(knx_source: str, knx_group_addr: str, value):
    """Builds a KNX message (cEMI) to write a value to a group address."""
    cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req)
    cemi.cemi_data.source_address = knx_source
    cemi.cemi_data.destination_address = "1/1/1"
    cemi.cemi_data.acpi = ACPI.groupvaluewrite
    cemi.cemi_data.data = int(value)
    return cemi

###############################################################################
# SEND REQUESTS                                                               #
###############################################################################

def tunneling_request(knxnet: KNXnet, channel: int, cemi: Packet) -> KNXPacket:
    """Sends a tunneling request with a specified cEMI message.
    The server first replies with an ack, then the response (or at least we 
    hope it will arrive in this order x)).
    We need to ack back after receiving the response.
    """
    tun_req = KNXPacket(type=SID.tunneling_request)
    tun_req.communication_channel_id = channel
    tun_req.cemi = cemi
    tun_req.show2()
    ack, _ = knxnet.sr(tun_req)
    ack.show2()
    response, _ = knxnet.receive()
    response.show2()
    # We have to ACK when we receive tunneling requests
    if response.sid == SID.tunneling_request and \
       tun_req.message_code == CEMI.l_data_req:
        ack = KNXPacket(type=SID.tunneling_ack, communication_channel_id=channel)
        knxnet.send(ack)
    return response

###############################################################################
# READ / WRITE                                                                #
###############################################################################

def group_write(ip: str, knx_group_addr: str, value, port: int=3671) -> KNXPacket:
    """Writes value to KNX group address via the server at address ip.
    We first need to establish a tunneling connection so that we can reach
    underlying device groups.
    """
    # Start tunneling connection
    knxnet, channel, knx_source = connect_tunneling(ip, port)
    cemi = cemi_group_write(knx_source, knx_group_addr, value)
    response = tunneling_request(knxnet, channel, cemi)
    # End tunneling connection
    disconnect_tunneling(knxnet, channel)
    return response
