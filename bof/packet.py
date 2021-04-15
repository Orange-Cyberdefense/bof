"""A BOFPacket represents a frame or part of one (a block), that contains
 packets and fields.

A BOFPacket uses a Scapy Packet object as attribute, as BOF protocol
implementations are based on Scapy.

The Scapy Packet is used as a basis for BOF to manipulate frames with its
own syntax. However, you can still perform "Scapy stuff" on the packet by
directly accessing BOFPacket.scapy_pkt attribute.

Note that BOFPacket DOES NOT inherit from Scapy packet, because we don't need
a "specialized" class, but a "translation" from BOF usage to Scapy objects.

Example (keep in mind that BOFPacket should not be instantiated directly :))::

    TODO:: add example of BOF final syntax + Scapy usage

"""
from random import randint

from scapy.packet import Packet
from scapy.fields import Field

from copy import deepcopy


class BOFPacket(object):
    """Representation of a network packet in BOF.

    A BOFPacket represents a frame or part of one (a block), that contains
    packets and fields.

    This class should not be instantiated directly but protocol-specific
    Packet class in BOF shall inherit it.

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

    def show(self, dump=False, indent=3, lvl="", label_lvl=""):
        return self.scapy_pkt.show(dump=dump, indent=indent, lvl=lvl, label_lvl=label_lvl)

    def show2(self, dump=False, indent=3, lvl="", label_lvl=""):
        return self.scapy_pkt.show2(dump=dump, indent=indent, lvl=lvl, label_lvl=label_lvl)

    def add_payload(self, other, autobind=False):
        """Adds the ``other`` Scapy payload to the ``BOFPacket``'s scapt_pkt
         attribute.

        This method's behavior is similar to the following code::

            self.scapy_pkt = self.scapy_pkt / other

        It adds the following features::

        - Independently add a ``BOFPacket`` or Scapy ``Packet`` as payload of the
        current ``BOFPacket``
        - Create a binding "on the fly" between the packet and it's payload if it
        was not defined in Scapy's implementation

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

            # Adding an "unexpected" payload (here TCP after HTTP)
            # with automatic rebinding :
            bof_pkt.add_payload(HTTP())
            bof_pkt.add_payload(TCP(), automatic_binding=True)
        """
        if isinstance(other, BOFPacket):
            other = other.scapy_pkt

        # Gets the last payload of our packet because this is the one we want to bind to the next payload
        last_layer = self.scapy_pkt.lastlayer()

        # Checks if a binding is found between our last layer and the `other` class
        # (bindings are defined as a list of tuples `layer.payload_guess`)
        other_in_payload_guess = any(other.__class__ in binding for binding in last_layer.payload_guess)

        # If no binding found and that we want to automatically add one
        if isinstance(other, Packet) and autobind and not other_in_payload_guess:
            # we may also use Scapy builtin bind_layers or pkt.decode_payload_as()
            last_layer.payload_guess.insert(0, ({}, other.__class__))

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


def clone_pkt_class(packet, name):
    """Replaces the Scapy `packet` class by a new class being the exact copy
    of itself. This is a trick used when we need to modify a Packet class
    attribute without affecting all object instance (eg: fields_desc to
    dynamically add a new field).

    :param packet: the Scapy Packet to update
    :param name: the new class name for packet

    Example::

        scapy_pkt1 = SNMP()
        scapy_pkt2 = SNMP()
        clone_pkt_class(scapy_pkt1, "SNMP2")
        scapy_pkt1.fields_desc.append(new_field)

        As a result, scapy_pkt2 won't contain the new field.
    """
    # Checks if a binding is found between our packet and its preceding layer for later use
    # (bindings are defined as a list of tuples `layer.payload_guess`)
    in_payload_guess = any(packet.__class__ in binding for binding in packet.underlayer.payload_guess)
    # Duplicates our packet class and replaces it by the clone
    class_copy = type(name, (packet.__class__,), {})
    packet.__class__ = class_copy
    # Bindings with the preceding layer must be done again
    if in_payload_guess:
        # we may also use Scapy builtin bind_layers or pkt.decode_payload_as()
        packet.underlayer.payload_guess.insert(0, ({}, packet.__class__))


def add_field(packet, new_field, value=None):
    """Adds a new Scapy field at the end of the specified ``packet``.

    :param packet: the Scapy packet/layer to update with a new field
    :param new_field: the Scapy Field to add at the end of the packet
    :param value: a value assigned to the new field

    Example::

        # Basic
        scapy_pkt = SNMP()
        new_field = ByteField("new_field", 0x42)
        add_field(scapy_pkt, new_field, 0x43)

        # With multiple layers
        scapy_pkt = TCP()/HTTP()
        new_field = ByteField("new_field", 0x42)
        add_field(scapy_pkt.getlayer(HTTP), new_field)
    """
    # Because we are going to edit `packet`'s class fields, we first need
    # to replace the class by a new one
    # (for now we use a random name to avoid duplicates but we may just increment it somehow ?)
    clone_pkt_class(packet, packet.__class__.__name__ + str(randint(1000000, 9999999)))

    # We reproduce the task performed during a Packet's fields init, but
    # adapt them to a single field addition
    # To make things simpler and straightforward, we started with no cache,
    # but we might implement it later
    packet.fields_desc.append(new_field)

    # Similar to Packet's do_init_fields() but for a single field
    packet.fieldtype[new_field.name] = new_field
    if new_field.holds_packets:
        packet.packetfields.append(new_field)
    packet.default_fields[new_field.name] = deepcopy(new_field.default)

    # Similar to the "strange initialization" (lines 164-179 of Scapy
    # Packet constructor) but for a single field
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

    if value is not None:
        packet.new_field = value
