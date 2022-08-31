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
        return "[{0}] Device name: {1}\n\tDescription: {2}\n\tMAC address: {3}" \
            "\n\tIP address: {4}".format(self.protocol, self.name, self.description,
                                         self.mac_address, self.ip_address)
