"""
KNX device
-------------

Object representation of a device that communicates using KNXnet/IP.

Relies on **KNX Standard v2.1**
"""

# Scapy
# from scapy.contrib import knx as scapy_knx
from bof.layers.raw_scapy import knx as scapy_knx

# Internal
from ... import BOFDevice, BOFNetworkError
from .knx_constants import MULTICAST_ADDR, PORT
from .knx_packet import KNXPacket

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
