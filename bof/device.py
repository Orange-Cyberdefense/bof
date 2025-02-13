"""Global object for representing industrial devices.

All objects in layers built using data extracted from responses to
protocol-specific discovery requests shall inherit ``BOFDevice``.
"""

from . import BOFProgrammingError

# Requires unit testing
class BOFDevice(object):
    """Interface class for devices, to inherit in layer-specific device classes.

    Device objects are usually built from device description requests in layers.
    We can collect different information about a device depending on its type
    and the protocol used. That is why BOFObject must be overriden in layers to
    store more details given. Only the name and IP address are known for sure.
    """
    protocol = "BOF"
    _attributes = {
        # Device identification
        "name": "Name",
        "description": "Description",
        "organisation": "Organisation",
        "vendor_id": "Vendor identifier",
        "device_id": "Device identifier",
        "serial_number": "Serial number",
        # Transport layer
        "ip_address": "IP address",
        "ip_netmask": "IP netmask",
        "ip_gateway": "IP gateway",
        "port": "Port",
        "multicast_address": "Multicast address",
        # Ethernet layer
        "mac_address": "MAC address",
        # Specific. TODO: Move in layers? Requires extra code to overload...
        "knx_address": "KNX individual address",
        # Physical layer
        "chassis_id": "Chassis identifier",
        "port_id": "Port identifier",
        "port_desc": "Port description",
        "capabilities": "Capabilities"
    }

    def __init__(self, **kwargs):
        # We create all arguments in the attributes list with empty values
        for k, v in self._attributes.items():
            setattr(self, k, None)
        # Now we set the values from kwargs :)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def name(self, attribute: object) -> str:
        """Returns the name of an attribute as str."""
        for name in self.__dict__:
            try:
                if self.__dict__[name] is attribute:
                    return name
            except KeyError:
                pass
        raise BOFProgrammingError("Attribute not found in object.")

    def title(self, attribute: object) -> str:
        """Returns the title associated to an attribute from known list.

        Example:
        If attribute is self.description: as the dictionary self._attributes
        contains a key "description" this method will return the value
        associated to this key (the title "Description").

        If the attribute's name is not in the attributes' list, the attribute's
        name is returned as is.
        """
        for name in self.__dict__:
            try:
                if self.__dict__[name] is attribute:
                    if name in self._attributes.keys():
                        return self._attributes[name]
                    return name
            except KeyError:
                pass
        raise BOFProgrammingError("Attribute not found in object.")
    
    @property
    def attributes(self) -> list:
        """Return the list of attributes if their name is in our list."""
        return [getattr(self, x) for x in self._attributes.keys() if x in self.__dict__]
            
    @property
    def properties(self) -> list:
        """Return the list of properties set to a device (list of str)."""
        props = []
        for name in self._attributes.keys():
            if getattr(self, name):
                props.append(name)
        return props
            
    def __str__(self):
        res = []
        for attr in self.attributes:
            if attr:
                res.append(" |_ {0}: {1}".format(self.title(attr), attr))
        return "\n".join(res)
