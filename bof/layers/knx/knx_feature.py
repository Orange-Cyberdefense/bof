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

###############################################################################
# DISCOVERY                                                                   #
###############################################################################

def search(ip: object=MULTICAST_ADDR, port: int=KNX_PORT) -> object:
    """Search for KNX devices on an network (multicast, unicast address(es).
    Sends a SEARCH REQUEST per IP and expects one SEARCH RESPONSE per device.
    **KNX Standard v2.1**

    :param ip: Multicast, unicast IPv4 address or list of such addresses to
               search for.  Default value is default KNXnet/IP multicast
               address 224.0.23.12.
    :param port: KNX port, default is 3671.
    :returns: The list of responding KNXnet/IP devices in the network.
    :raises BOFProgrammingError: if IP is invalid.
    """
    devices = []
    if isinstance(ip, str):
        ip = [ip]
    for i in ip:
        try:
            ip_address(i)
        except ValueError:
            raise BOFProgrammingError("Invalid IP {0}".format(i)) from None
            return
        # Start searching
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
