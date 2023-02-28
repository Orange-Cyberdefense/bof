"""Global object for representing industrial devices.

All objects in layers built using data extracted from responses to
protocol-specific discovery requests shall inherit ``BOFDevice``.
"""
class BOFDevice(object):
    """Interface class for devices, to inherit in layer-specific device classes.

    Device objects are usually built from device description requests in layers.
    A device has a set of basic information: a name, a description, a MAC
    address and an IP address. All of them are attributes to this base object,
    but not all of them may be provided when asking protocols for device
    descriptions. On the other hand, most of protocol-specific devices will have
    additional attributes.
    """
    protocol:str = "BOF"
    name:str = None
    description:str = None
    mac_address:str = None
    ip_address:str = None

    # Requires unit testing
    def __init__(self, name: str=None, description: str=None,
                 mac_address: str=None, ip_address: str=None):
        self.name = name
        self.description = description
        self.mac_address = mac_address
        self.ip_address = ip_address
        
    def __str__(self):
        data = ["[{0}] Device name: {1}".format(self.protocol, self.name)]
        if self.description:
            data += ["Description: {0}".format(self.description)]
        if self.mac_address:
            data += ["MAC address: {0}".format(self.mac_address)]
        if self.ip_address:
            data += ["IP address: {0}".format(self.ip_address)]
        return "\t\n".join(data)
