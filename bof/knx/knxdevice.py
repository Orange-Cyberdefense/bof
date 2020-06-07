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

from .knxnet import KnxNet, MULTICAST_ADDR, PORT
from .knxframe import KnxFrame

###############################################################################
# KNX DEVICE GLOBAL METHODS                                                   #
###############################################################################

def search(addresses:str=MULTICAST_ADDR, port:int=PORT) -> list:
    """Search for KNX devices using multicast or on a given address range.

    Sends a SEARCH REQUEST to an endpoint, expects a SEARCH RESPONSE.

    :param addresses: IPv4 address/range (``A.B.C.D/S``), default: multicast.
    :param port: Default KNX port is 3671 but can be changed.
    :returns: A list of IPv4 addresses corresponding to reached KNX devices.
    """
    pass # TODO

def discover(addresses, port:int=PORT) -> object:
    """Gathers information about KNX devices at a given address or range.

    Sends a DESCRIPTION REQUEST, expects a DESCRIPTION RESPONSE.

    :param addresses: IPv4 address, range or ``KnxNet`` connection object.
                      If range, we first ``search()`` for valid objects 
                      before asking them to describe themselves.
    :param port: Default KNX port is 3671 but can be changed.
    :returns: Either a ``KnxDevice`` object or a list of such objects.
    """
    # Check what type addresses and format it
    if (isinstance(addresses, str)):
        # TODO: Condition single IPv4 address, use ipaddress lib
        knxnet = KnxNet().connect(addresses, port)
        # TODO: COndition IPv4 address range, use ipaddress lib
        device_addresses = search(addresses)
        device_objects = []
        for address in device_addresses:
            device_object.append(discover(address, port))
        return device_objects
    if (isinstance(addresses, KnxNet)):
        knxnet = addresses
    else:
        raise BOFProgrammingError("discover() expects IPv4 or KnxNet.")
    # Discover
    description_request = KnxFrame(type="DESCRIPTION REQUEST")
    description_request.body.ip_address.value = knxnet.source_address
    description_request.body.port.value = knxnet.source_port
    description_response = knxnet.send(description_request)
    return KnxDevice(description_response)

###############################################################################
# KNX DEVICE OBJECT                                                           #
###############################################################################

class KnxDevice():
    """A ``KnxDevice`` carries data related to a given KNXnet/IP server.

    :param name: Friendly name of the device.
    :param address: Network address as a tuple ``(IPv4 address, port)``.
    :param channel: Channel on which the device is connected currently, if
                    it is. Channel is 0 if not connected.

    TODO
    """
    name:str
    address:tuple

    def __init__(self, description:KnxFrame=None, **kwargs):
        """Initialize the device from scratch or using a description (content
        of a DESCRIPTION RESPONSE frame.
        """
        self.name = kwargs["name"] if "name" in kwargs else ""
        self.address = kwargs["address"] if "address" in kwargs else ("", PORT)
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
