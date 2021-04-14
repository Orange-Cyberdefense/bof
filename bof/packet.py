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
from random import randint

from scapy.packet import Packet, bind_layers
from scapy.fields import Field

import copy


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

    # def __str__(self):
    #     return "{0}: {1}".format(self.__class__.__name__, self.name)

    def __getattr__(self, attr):
        return self.scapy_pkt.__getattr__(attr)

    def __iter__(self):
        yield from self.scapy_pkt.fields_desc

    def __div__(self, other):
        """Adds the ``other`` ``BOFPacket``'s Scapy payload to the current``BOFPacket``.
        Note that contrary to ``add_payload``, this works only with ``BOFPacket``, with
        an automatic binding by default too.

        This method's behavior is similar to the following code::

            self.scapy_pkt = self.scapy_pkt / other_bof_pkt.scapy_pkt

        Additional features::

        - Create a binding "on the fly" if it was not defined in Scapy's implementation

        :param other: BOF packet to add as payload.

        Example::

            # Adding a BOF packet as payload to the current scapy_pkt :
            bof_pkt1.scapy_pkt = TCP()
            bof_pkt2.scapy_pkt = ModbusADURequest()
            bof_pkt3 = bof_pkt1 / bof_pkt2

        :TODO: better test extreme cases for the method (same as add_payload)
        :TODO: see if adding scapy_pkt to each other is enough ? (loss of bof_pkt attributes)
        """

        other = other.scapy_pkt

        # Checks if a binding is found between `scapy_pkt` and `other class`
        # Bindings are defined as a list of tuples `self.scapy_pkt.payload_guess`
        other_in_payload_guess = any(other.__class__ in binding for binding in self.scapy_pkt.payload_guess)

        # If no binding found and that we want to automatically add one (for now : yes by default)
        if isinstance(other, Packet) and not other_in_payload_guess:
            self.scapy_pkt.payload_guess.insert(0, ({}, other.__class__))
            # We may use bind_layers function family instead of editing payload_guess
            # directly, something like : bind_layers(self.scapy_pkt.__class__, other.__class__)
            pass
        return self.scapy_pkt / other

    __truediv__ = __div__

    def show(self, dump=False, indent=3, lvl="", label_lvl=""):
        return self.scapy_pkt.show(dump=dump, indent=indent, lvl=lvl,
                                   label_lvl=label_lvl)

    def show2(self, dump=False, indent=3, lvl="", label_lvl=""):
        return self.scapy_pkt.show2(dump=dump, indent=indent, lvl=lvl,
                                    label_lvl=label_lvl)

    def add_payload(self, other, autobind=False):
        """Adds the ``other`` Scapy payload to the ``BOFPacket``'s scapy
        packet attribute.

        This method's behavior is similar to the following code::

            self.scapy_pkt = self.scapy_pkt / other

        Additional features::

        - Bind the ``BOFPacket`` to a Scapy Packet or to an other ``BOFPacket``
        - Create a binding "on the fly" if it was not defined in Scapy's implementation

        :param other: Scapy or BOF packet to add as payload.
        :param autobind: Whether or not unspecified binding found in Scapy
                                  implementation are automatically added.

        Example::

            # Adding a Scapy packet as payload to the current scapy_pkt :
            bof_pkt.scapy_pkt = TCP()
            bof_pkt.add_payload(ModbusADURequest())

            # Adding a BOF packet as payload to the current scapy_pkt :
            bof_pkt1.scapy_pkt = TCP()
            bof_pkt2.scapy_pkt = ModbusADURequest()
            bof_pkt1.add_payload(bof_pkt2)

            # Adding a unexpected payload, performing the binding automatically
            bof_pkt.add_payload(TCP(), automatic_binding=True)
            bof_pkt.add_payload(TCP())
            # Because two TCP layers aren't supposed to be bound together,
            # a binding is automatically added

        :TODO: better test extreme cases for the method
        :TODO: see if adding scapy_pkt to each other is enough ? (loss of bof_pkt attributes)
        """
        if isinstance(other, BOFPacket):
            other = other.scapy_pkt

        # Gets the last payload of our packet, because this is the one we want to bind to the next payload
        last_layer = self.scapy_pkt.lastlayer()

        # Checks if a binding is found between our last layer and `other class`
        # Bindings are defined as a list of tuples `layer.payload_guess`
        other_in_payload_guess = any(other.__class__ in binding for binding in last_layer.payload_guess)

        # If no binding found and that we want to automatically add one
        if isinstance(other, Packet) and autobind and not other_in_payload_guess:
            last_layer.payload_guess.insert(0, ({}, other.__class__))
            # We may also use bind_layers function family instead of editing payload_guess
            pass
        self.scapy_pkt = self.scapy_pkt / other

    @property
    def name(self) -> str:
        return self.scapy_pkt.name

    @name.setter
    def name(self, name: str) -> None:
        self.scapy_pkt.name = name

    @property
    def fields(self):
        """Returns the list of fields in packet and subpackets."""
        fieldlist = []
        for item in self:
            if isinstance(item, BOFPacket):
                fieldlist += item.fields
            elif isinstance(item, Field):
                fieldlist.append(item)
        return fieldlist


def _replace_pkt_class(packet, new_class_name):
    """:TODO:"""
    in_payload_guess = any(packet.__class__ in binding for binding in packet.underlayer.payload_guess)
    new_class = type(new_class_name, (packet.__class__,), {})
    packet.__class__ = new_class
    if in_payload_guess:
        packet.underlayer.payload_guess.insert(0, ({}, packet.__class__))


def _add_field(packet, new_field, value=None):
    """
    :TODO: docstring
    :TODO: Option to add a field wherever we want in the packet (=> insert
           at the right place)
    :TODO: Test, including complex fields like PacketField or MultipleTypeField
    :TODO: Automatically replace duplicated field names to access the right
           member as property
    :TODO: Add guess_payload override to handle specific case ? (=> in BOF
           protocol implementations ?)
    """
    # Because we are going to edit packet's class fields, we first need to replace the class by a new one
    # For now we use a random name just to check it works but we should just increment it
    _replace_pkt_class(packet, packet.__class__.__name__ + str(randint(1000000, 9999999)))

    # We reproduce the task performed during a Packet's fields init, but
    # adapt them to a single field addition
    # To make things simpler and straightforward, we started with no cache,
    # but we might implement it later
    packet.fields_desc.append(new_field)

    # Similar to Packet's do_init_fields() but for a single field
    packet.fieldtype[new_field.name] = new_field
    if new_field.holds_packets:
        packet.packetfields.append(new_field)
    packet.default_fields[new_field.name] = copy.deepcopy(new_field.default)

    # Similar to the "strange initialization" (lines 164-179 of the
    # constructor) but for a single field
    fname = new_field.name
    try:
        value = packet.fields.pop(fname)
        packet.fields[fname] = packet.get_field(fname).any2i(packet, value)
    except KeyError:
        pass

    if fname in packet.fields and fname in packet.deprecated_fields:
        value = packet.fields[fname]
        fname = packet._resolve_alias(fname)
        packet.fields[fname] = packet.get_field(fname).any2i(packet, value)

    if value != None:
        packet.new_field = value
