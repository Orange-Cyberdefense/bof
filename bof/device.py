"""Global object for representing industrial devices.

All objects in layers built using data extracted from responses to
protocol-specific discovery requests shall inherit ``BOFDevice``.
"""
class BOFDevice(object):
    """Interface class for devices, to inherit in layer-specific device classes.

    Device objects are usually built from device description requests in layers.
    We can collect different information about a device depending on its type
    and the protocol used. That is why BOFObject must be overriden in layers to
    store more details given. Only the name and IP address are known for sure.
    """
    protocol:str = "BOF"
    name:str = None
    ip_address:str = None

    # Requires unit testing
    def __init__(self, name: str=None, ip_address: str=None):
        self.name = name
        self.ip_address = ip_address
        
    def __str__(self):
        return "[{0}] Results for {1} (2)".format(
            self.protocol, self.name, self.ip_address)
