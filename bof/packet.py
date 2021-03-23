"""TODO
"""

from scapy.packet import Packet

class BOFPacket(object):
    """Representation of a network packet in BOF. Base class for BOF "layers".

    A packet can be a complete frame or part of one (a block), as long as it contains
    either a set of packets, a set of fields, or both.

    THis class should not be instantiated directly but Packet class in BOF layers
    shall inherit it.

    Example::

        class OtterPacket(BOFPacket)

    A BOFPacket object uses a Scapy-based Packet object, as protocol implementations
    are based on Scapy. The Scapy raw packet object is an attribute of a BOFPacket
    object, which uses it to manipulate the BOF usually manipulates packets.
    However, you can perform direct "Scapy" stuff on the packet by accessing directly
    BOFPacket.scapy_pkt attribute.

    Example (keep in mind that BOFPacket should not be instantiated directly :))::

        pkt = BOFPacket()
        pkt.scapy_pkt.show()

    BOFPacket DOES NOT inherit from Scapy packet, because we don't need a
    "specialized" class, but a "translation" from BOF usage to Scapy objects.
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

    @property
    def name(self) -> str:
        return self.scapy_pkt.name
    @name.setter
    def name(self, name:str) -> None:
        self.scapy_pkt.name = name
