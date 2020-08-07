"""
KNX device management
---------------------

Upper-level classes and methods for KNX devices discovery and handling on a
KNXnet/IP network. Builds and uses ``KnxDevice`` objects.

WARNING: Unlike KnxFrame and KnxNet objects, upper-level content is bound to 
the KNX specifications. Currently: **KNX Standard v2.1**.

Available methods:

:search(): Search for KNX devices on a subnetwork.
:discover(): Gather information about one or more KNX devices.

A KnxDevice object carries data gathered on a device, for further usage and
manipulation by the end-user.
"""

import ipaddress

from .. import byte, BOFNetworkError, BOFProgrammingError
from .knxnet import KnxNet, MULTICAST_ADDR, PORT
from .knxframe import KnxFrame

###############################################################################
# KNX DEVICE GLOBAL METHODS                                                   #
###############################################################################

def search(addresses:str=MULTICAST_ADDR, port:int=PORT) -> list:
    """Search for KNX devices using multicast or on a given address range.

    Sends a SEARCH REQUEST to an endpoint, expects a SEARCH RESPONSE.

    :param addresses: IPv4 address/range (``A.B.C.D/S``), default: multicast
                      (not implemented yet)
    :param port: Default KNX port is 3671 but can be changed.
    :returns: A list of IPv4 addresses corresponding to reached KNX devices.
    """
    def __search_req(knxnet):
        search_request = KnxFrame(type="SEARCH REQUEST")
        search_request.body.ip_address.value = knxnet.source_address
        search_request.body.port.value = knxnet.source_port
        return search_request

    responding_devices = []
    knxnet = KnxNet()
    # TODO: Implement multicast SEARCH_REQUEST
    try:
        for ip in ipaddress.ip_network(addresses):
            try:
                knxnet.connect(ip, port)
                knxnet.send_receive(__search_req(knxnet), timeout=0.01)
                responding_devices.append(str(ip))
            except BOFNetworkError:
                pass # Timed out or connection refised, let's move on
            finally:
                knxnet.disconnect()
    except ValueError:
        raise BOFProgrammingError("IP range is invalid. (should have format X.X.X.0/24)") from None
    return responding_devices

def discover(addr, port:int=PORT) -> object:
    """Gathers information about KNX devices at a given address or range.

    Sends a DESCRIPTION REQUEST, expects a DESCRIPTION RESPONSE.

    :param addr: IPv4 address, range or ``KnxNet`` connection object. If
                 range, we first ``search()`` for valid objects before
                 asking them to describe themselves.
    :param port: Default KNX port is 3671 but can be changed.
    :returns: Either a ``KnxDevice`` object or a list of such objects.
    """
    def __descr_req(knxnet):
        description_request = KnxFrame(type="DESCRIPTION REQUEST")
        description_request.body.ip_address.value = knxnet.source_address
        description_request.body.port.value = knxnet.source_port
        return description_request

    if (isinstance(addr, KnxNet)):
        description_response = addr.send_receive(__descr_req(addr), timeout=0.5)
        return KnxDevice(description_response, ip_address=addr.source_address,
                         port=addr.source_port)
    if (isinstance(addr, str)):
        try: # Is it a single IPv4 address?
            ipaddress.ip_address(addr)
            knxnet = KnxNet().connect(addr, port)
            description_response = knxnet.send_receive(__descr_req(knxnet), timeout=0.1)
            knxnet.disconnect()
        except ValueError:
            pass
        except BOFNetworkError:
            knxnet.disconnect()
            return None
        else:
            return KnxDevice(description_response, ip_address=addr, port=port)
        # Apparently it is not.
        device_objects = []
        if "," in addr: # List of IP expected
            for address in addr.split(","):
                device = discover(address, port)
                if device:
                    device_objects.append(device)
        else: # Range ?
            device_addresses = search(addr)
            for address in device_addresses:
                device_objects.append(discover(address, port))
        return device_objects
    else:
        raise BOFProgrammingError("discover() expects IPv4 addr/list/range or KnxNet.")
    return None

###############################################################################
# KNX DEVICE OBJECT                                                           #
###############################################################################

class KnxDevice():
    """A ``KnxDevice`` carries data related to a given KNXnet/IP server.

    :param name: Friendly name of the device.
    :param ip_address: Device IPv4 address.
    :param knx_address: Device KNX individual address.
    :param mac_address: Device MAC address.
    :param port: Device port on which we connect.
    :param channel: Channel on which the device is connected currently, if
                    it is. Channel is 0 if not connected.

    TODO
    """
    __name:str
    __ip_address:str
    __knx_address:str
    __mac_address:str
    __port:int

    def __init__(self, description:KnxFrame=None, **kwargs):
        """Initialize the device from scratch or using a description (content
        of a DESCRIPTION RESPONSE frame).
        """
        self.name = kwargs["name"] if "name" in kwargs else ""
        self.ip_address = kwargs["ip_address"] if "ip_address" in kwargs else ""
        self.knx_address = kwargs["knx_address"] if "knx_address" in kwargs else ""
        self.mac_address = kwargs["mac_address"] if "mac_address" in kwargs else ""
        self.port = kwargs["port"] if "port" in kwargs else PORT
        if description:
            self.add_description(description)

    def __str__(self):
        return "{0}: Name={1}, MAC={2}, IP={3}:{4} KNX={5}".format(
            self.__class__.__name__, self.name, self.mac_address,
            self.ip_address, self.port, self.knx_address)

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def add_description(self, description:KnxFrame):
        """Uses the content of a DESCRIPTION RESPONSE frame returned by a
        KNXnet/IP server to fill in information about the device.

        :param description: ``KnxFrame`` object for a DESCRIPTION RESPONSE.
        """
        # TODO: So far we manually add some fields from device hardware
        # (DIB_DEVICE_INFO) from DESCRIPTION_RESPONSE, some may be added later
        self.name = description.body.device_hardware.friendly_name.value
        self.mac_address = description.body.device_hardware.mac_address.value
        self.knx_address = description.body.device_hardware.knx_individual_address.value


    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def name(self) -> str:
        return self.__name
    @name.setter
    def name(self, value:str):
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        if not isinstance(value, str):
            raise BOFProgrammingError("Name must be a string.")
        self.__name = value
    @property
    def ip_address(self) -> str:
        return self.__ip_address
    @ip_address.setter
    def ip_address(self, value:str):
        if isinstance(value, bytes):
            value = byte.to_ipv4(value)
            print(value)
        try:
            if len(value):
                ipaddress.ip_address(value)
            self.__ip_address = value
        except ValueError:
            raise BOFProgrammingError("Device expects an IPv4 address.") from None
    @property
    def mac_address(self) -> str:
        return self.__mac_address
    @mac_address.setter
    def mac_address(self, value:str):
        if isinstance(value, bytes):
            value = byte.to_mac(value)
        if not isinstance(value, str):
            raise BOFProgrammingError("Mac address must be a string.")
        self.__mac_address = value
    @property
    def knx_address(self) -> str:
        return self.__knx_address
    @knx_address.setter
    def knx_address(self, value:str):
        self.__knx_address = byte.to_knx(value)
    @property
    def port(self) -> str:
        return self.__port
    @port.setter
    def port(self, value:str):
        if isinstance(value, bytes):
            value = byte.to_int(value)
        if not isinstance(value, int):
            raise BOFProgrammingError("Port must be an integer.")
        self.__port = value
