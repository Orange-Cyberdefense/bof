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

from ipaddress import ip_address, ip_network

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
        for ip in ip_network(addresses):
            knxnet.connect(ip, port)
            try:
                knxnet.send_receive(__search_req(knxnet), timeout=0.01)
                responding_devices.append(str(ip))
            except BOFNetworkError:
                pass # Timed out, let's move on
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
        return KnxDevice(description_response, address=addr.source_address,
                         port=addr.source_port)
    if (isinstance(addr, str)):
        try: # Is it a single IPv4 address?
            ip_address(addr)
            knxnet = KnxNet().connect(addr, port)
            description_response = knxnet.send_receive(__descr_req(knxnet), timeout=0.1)
            knxnet.disconnect()
        except ValueError:
            pass
        except BOFNetworkError:
            knxnet.disconnect()
            return None
        else:
            return KnxDevice(description_response, address=addr, port=port)
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
    :param address: Device IPv4 address.
    :param port: Device port on which we connect.
    :param channel: Channel on which the device is connected currently, if
                    it is. Channel is 0 if not connected.

    TODO
    """
    __name:str
    __address:str
    __port:int

    def __init__(self, description:KnxFrame=None, **kwargs):
        """Initialize the device from scratch or using a description (content
        of a DESCRIPTION RESPONSE frame.
        """
        self.name = kwargs["name"] if "name" in kwargs else ""
        self.address = kwargs["address"] if "address" in kwargs else ""
        self.port = kwargs["port"] if "port" in kwargs else PORT
        if description:
            self.add_description(description)

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def add_description(self, description:KnxFrame):
        """Uses the content of a DESCRIPTION RESPONSE frame returned by a
        KNXnet/IP server to fill in information about the device.

        :param description: ``KnxFrame`` object for a DESCRIPTION RESPONSE.
        """
        # TODO. Example:
        self.name = description.body.device_hardware.friendly_name.value
        # TODO: Maybe add the attributes automatically according to properties?
        # ex: description.body.device_hardware.mac_address becomes self.mac_address

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
    def address(self) -> str:
        return self.__address
    @address.setter
    def address(self, value:str):
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        try:
            ip_address(value)
            self.__address = value
        except ValueError:
            raise BOFProgrammingError("Device expects an IPv4 address.") from None
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
