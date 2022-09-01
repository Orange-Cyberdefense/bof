"""
KNX functions
-------------

Higher-level functions to interact with devices using KNXnet/IP.

Contents:

:KNXDevice:
    Object representation of a KNX device with multiple properties. Only
    supports KNXnet/IP servers so far, but will be extended to KNX devices.
:Functions:
    High-level functions to interact with a device: search, discover, read,
    write, etc.

Relies on **KNX Standard v2.1**
"""

from ipaddress import ip_address
# Internal
from ... import BOFNetworkError, BOFProgrammingError, BOFDevice, IS_IP
from .knx_network import *
from .knx_packet import *
from .knx_messages import *
from ...layers.raw_scapy import knx as scapy_knx 

def INDIV_ADDR(x: int) -> str:
    """Converts an int to KNX individual address."""
    return "%d.%d.%d" % ((x >> 12) & 0xf, (x >> 8) & 0xf, (x & 0xff))

def GROUP_ADDR(x: int) -> str:
    """Converts an int to KNX group address."""
    return "%d/%d/%d" % ((x >> 11) & 0x1f, (x >> 8) & 0x7, (x & 0xff))

###############################################################################
# KNX DEVICE REPRESENTATION                                                   #
###############################################################################

class KNXDevice(BOFDevice):
    """Object representing a KNX device.

    Data stored to the object is the one returned by SEARCH RESPONSE and
    DESCRIPTION RESPONSE messages, stored to public attributes::

      Device name, IPv4 address, KNXnet/IP port, KNX individual address, MAC
      address, KNX multicast address used, device serial number.

    This class provides two factory class methods to build a KNXDevice object
    from search responses and description responses.

    The information gathered from devices may be completed, improved later.
    """
    protocol:str = "KNX"
    def __init__(self, name: str, ip_address: str, port: int, knx_address: str,
                 mac_address: str, multicast_address: str=MULTICAST_ADDR,
                 serial_number: str=""):
        self.name = name
        self.description = None
        self.ip_address = ip_address
        self.port = port
        self.knx_address = knx_address
        self.mac_address = mac_address
        self.multicast_address = multicast_address
        self.serial_number = serial_number

    def __str__(self):
        return "{0}\n\tPort: {1}\n\tMulticast address: {2}\n\t" \
            "KNX address: {3}\n\tSerial number: {4}".format(
                super().__str__(), self.port, self.multicast_address,
                self.knx_address, self.serial_number)

    @classmethod
    def init_from_search_response(cls, response: KNXPacket):
        """Set appropriate values according to the content of search response.

        :param response: Search Response provided by a device as a KNXPacket.
        :returns: A KNXDevice object.

        Uage example::

          responses = KNXnet.multicast(search_request(), (ip, port))
          for response, source in responses:
            device = KNXDevice.init_from_search_response(KNXPacket(response))
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
        :param source: Source of the response, usually provided in KNXnet's receive()
                       and sr() return values.
        :returns: A KNXDevice object.

        Usage example::

          response, source = knxnet.sr(description_request(knxnet))
          device = KNXDevice.init_from_description_response(response, source)
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
# FUNCTIONS                                                                   #
###############################################################################

#-----------------------------------------------------------------------------#
# Discovery                                                                   #
#-----------------------------------------------------------------------------#

def search(ip: object=MULTICAST_ADDR, port: int=KNX_PORT) -> list:
    """Search for KNX devices on an network using multicast.
    Sends a SEARCH REQUEST and expects one SEARCH RESPONSE per device.

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
    So far, only sends a DESCRIPTION REQUEST and uses the DESCRIPTION RESPONSE.
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

def group_write(ip: str, knx_group_addr: str, value, port: int=3671) -> None:
    """Writes value to KNX group address via the server at address ip.
    We first need to establish a tunneling connection so that we can reach
    underlying device groups.

    :param ip: IPv4 address of KNX device.
    :param knx_group_addr: KNX group address targeted (with format X/Y/Z)
                           Group addresses are defined in KNX project settings.
    :param value: Value to set the group address' content to.
    :param port: KNX port, default is 3671.
    :returns: Nothing
    :raises BOFProgrammingError: if IP is invalid.
    :raises BOFNetworkError: if device cannot be reached.
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

def individual_address_scan(ip: str, addresses: object, port: str=3671) -> bool:
    """Scans KNX gateway to find if individual address exists.
    We first need to establish a tunneling connection and use cemi connect
    messages on each address to find out which one responds.
    As the gateway will answer positively for each address (L_data.con), we
    also wait for L_data.ind which seems to indicate existing addresses.

    :param ip: IPv4 address of KNX device.
    :param address: KNx individual addresses as a string or a list.
    :param port: KNX port, default is 3671.
    :returns: A list of existing individual addresses.
    :raises BOFProgrammingError: if IP is invalid.

    Does not work (yet) for KNX gateways' individual addresses.
    Not reliable: Crashes after 60 addresses... Plz send help ;_;
    Also requires heavy refactoring after fixing issues.
    """
    IS_IP(ip)
    exists = []
    if not isinstance(addresses, list) and not isinstance(addresses, tuple):
        addresses = [addresses]

    knxnet = KNXnet().connect(ip, port)
    # Start tunneling connection
    response, source = knxnet.sr(connect_request_tunneling(knxnet))
    channel = response.communication_channel_id
    # Send cemi connect request, wait for ack and response, ack back
    seq = 0
    for address in addresses:
        print(address)
        c_connect = cemi_connect(address)
        ack, source = knxnet.sr(tunneling_request(channel, seq, c_connect)); seq+=1
        response, source = knxnet.receive()
        knxnet.send(tunneling_ack(channel, response.sequence_counter))
        # Sends cemi device description read, wait for ack and response
        c_read = cemi_dev_descr_read(address)
        ack, source = knxnet.sr(tunneling_request(channel, seq, c_read)); seq+=1
        response, source = knxnet.receive() # dev descr read con
        knxnet.send(tunneling_ack(channel, ack.sequence_counter))
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
            c_ack = cemi_ack(address)
            ack, source = knxnet.sr(tunneling_request(channel, seq, c_ack)); seq+=1
            response, source = knxnet.receive()
            knxnet.send(tunneling_ack(channel, response.sequence_counter))
            exists.append(address)
        except BOFNetworkError:
            # Boiboite did not reply with descr resp == device does not exist
            pass
        finally:
            # Send cemi disconnect request, wait for ack and response, ack back
            c_disco = cemi_disconnect(address)
            ack, source = knxnet.sr(tunneling_request(channel, seq, c_disco)); seq+=1
            response, source = knxnet.receive()
            knxnet.send(tunneling_ack(channel, response.sequence_counter))
    # End tunneling connection
    response, source = knxnet.sr(disconnect_request(knxnet, channel))
    knxnet.disconnect()
    return exists
    
def line_scan(ip: str, line: str="", port: int=3671) -> list:
    """Scans KNX gateway to find existing individual addresses on a line.
    We first need to establish a tunneling connection and use cemi connect
    messages on each address to find out which one responds.
    As the gateway will answer positively for each address (L_data.con), we
    also wait for L_data.ind which seems to indicate existing addresses.

    :param ip: IPv4 address of KNX device.
    :param line: KNX backbone to scan (default == empty == scan all lines
                 from 0.0.0 to 15.15.255)
    :param port: KNX port, default is 3671.
    :returns: A list of existing individual addresses on the KNX bus.

    Methods require smart detection of line, so far only line 1.1.X is
    supported and it is dirty.
    """
    # TODO: decent line parsing and handling
    if line.startswith("1.1."):
        begin, end = 4352, 4352+255
    else:
        begin, end = 0, 65635
    addr = [INDIV_ADDR(x) for x in range(begin, end)]
    return individual_address_scan(ip, addr, port)
