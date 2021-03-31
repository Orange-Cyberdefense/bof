"""A BOFPacket represents a complete frame or part of one (a block), as long
as it contains either a set of packets, a set of fields, or both.

It uses a Scapy-based Packet object, as protocol implementations
are based on Scapy. The Scapy raw packet object is an attribute of a BOFPacket
object, which uses it to manipulate the way BOF usually manipulates packets.
However, you can perform direct "Scapy" stuff on the packet by accessing directly
BOFPacket.scapy_pkt attribute.

Example (keep in mind that BOFPacket should not be instantiated directly :))::

    pkt = BOFPacket()
    pkt.scapy_pkt.show()

BOFPacket DOES NOT inherit from Scapy packet, because we don't need a
"specialized" class, but a "translation" from BOF usage to Scapy objects.
"""

from scapy.packet import Packet, bind_layers


class BOFPacket(object):
    """Representation of a network packet in BOF. Base class for BOF "layers".

    A packet can be a complete frame or part of one (a block), as long as it contains
    either a set of packets, a set of fields, or both.

    :param scapy_pkt: Scapy actual Packet object (inheriting from packet) and used by
                      BOF for protocol implementation-related stuff.

    This class should not be instantiated directly but Packet class in BOF layers
    shall inherit it.

    Example::

        class OtterPacket(BOFPacket)
    """
    scapy_pkt = None

    def __init__(self):
        self.scapy_pkt = Packet()
        self.scapy_pkt.name = self.__class__.__name__

    def __bytes__(self):
        return bytes(self.scapy_pkt)

    def __len__(self):
        return len(self.scapy_pkt)

    def __str__(self):
        return "{0}: {1}".format(self.__class__.__name__, self.name)

    def __iter__(self):
        yield from self.scapy_pkt

    def show(self):
        self.scapy_pkt.show()

    def add_payload(self, other, automatic_binding=False):
        """Adds the `other` Scapy payload to the BOFPacket's scapy packet attribute.

        This method's behavior is similar to `self.scapy_pkt = self.scapy_pkt / other` but adds additional options including :
            - the possibility to bind the BOFPacket either to a Scapy Packet or to an other BOFPacket
            - the possibility to create a binding "on the fly" if it was not defined in Scapy implementation

        :param other: Scapy or BOF packet to add as payload
        :param automatic_binding: Whether or not unspecified binding found in Scapy implementation are automatically added

        Example::

            Adding a Scapy packet as payload to the current scapy_pkt :
            bof_pkt.scapy_pkt = TCP()
            bof_pkt.add_payload(ModbusADURequest())

            Adding a BOF packet as payload to the current scapy_pkt :
            bof_pkt1.scapy_pkt = TCP()
            bof_pkt2.scapy_pkt = ModbusADURequest()
            bof_pkt1.add_payload(bof_pkt2)

            Adding a unexpected payload, performing the binding automatically
            bof_pkt.add_payload(TCP())
            bof_pkt.add_payload(TCP())
            Because two TCP layers aren't supposed to be bound together, a binding is automatically added

            # TODO: see if payload automatic binding option is actually necessary (to be understood in show2() the answer is yes, but do we really need it ?)
            # TODO: test the method
            # TODO consider the following syntax rather that updating the packet itself in the method : `bof_pkt = bof_pkt.addlayer(TCP())`
            # TODO: add '/' syntax (problem is that it is called by the element on the right of the division sign, on which we have no control)
            # TODO: add setter for scapy_pkt
        """
        if isinstance(other, BOFPacket):
            other = other.scapy_pkt

        # checks if a binding is found between `scapy_pkt` and `other class`
        # binding are defined as a list of tuples `self.scapy_pkt.payload_guess`
        other_in_payload_guess = any(other.__class__ in binding for binding in self.scapy_pkt.payload_guess)

        # if no binding found and that we want to automatically add one
        if isinstance(other, Packet) and automatic_binding and not other_in_payload_guess:
            self.scapy_pkt.payload_guess.insert(0, ({}, other.__class__))
            # we may use bind_layers function family instead of editing payload_guess directly, something like :
            # bind_layers(self.scapy_pkt.__class__, other.__class__)
            pass
        self.scapy_pkt = self.scapy_pkt / other

    @property
    def name(self) -> str:
        return self.scapy_pkt.name

    @name.setter
    def name(self, name: str) -> None:
        self.scapy_pkt.name = name
