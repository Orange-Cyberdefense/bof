"""Global object for representing industrial devices.

All objects in layers built using data extracted from responses to
protocol-specific discovery requests shall inherit ``BOFDevice``.
"""

from ipaddress import IPv4Address

# Requires unit testing
class BOFDevice(object):
    """Interface class for devices, to inherit in layer-specific device classes.

    Device objects are usually built from device description requests in layers.
    We can collect different information about a device depending on its type
    and the protocol used. That is why BOFObject must be overriden in layers to
    store more details given. Only the name and IP address are known for sure.
    """
    protocol:str = "BOF"
    name:str = None
    _ip_address:str = None

    def __init__(self, name: str=None, ip_address: str=None):
        self.name = name
        self._ip_address = ip_address

    @property
    def ip_address(self) -> IPv4Address:
        if not isinstance(self._ip_address, IPv4Address):
            return IPv4Address(self._ip_address)
        return self._ip_address
    @ip_address.setter
    def ip_address(self, ip:object) -> None:
        """Convert (if needed) and set IP address as a IPv4Address object."""
        if not isinstance(ip, IPv4Address):
            self._ip_address = IPv4Address(ip)
        else:
            self._ip_address = ip
        
    def __str__(self):
        return "[{0}] Results for {1} ({2})".format(
            self.protocol, self.name, self.ip_address)
