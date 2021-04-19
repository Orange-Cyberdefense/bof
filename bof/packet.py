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
from copy import deepcopy
# Scapy
from scapy.packet import Packet
from scapy.fields import Field
# Internal
from bof import BOFProgrammingError

###############################################################################
# BOFPacket class                                                             #
###############################################################################

class BOFPacket(object):
    """Representation of a network packet in BOF.

    A BOFPacket represents a frame or part of one (a block), that contains
    packets and fields.

    This class should not be instantiated directly but protocol-specific
    Packet class in BOF shall inherit it.

    :param _pkt: Raw Packet bytes used to build a frame (mostly done at reception)
    :param scapy_pkt: Scapy actual Packet object (inheriting from packet) and
                      used by BOF for protocol implementation-related stuff.

    Example::

        class OtterPacket(BOFPacket)
    """
    _scapy_pkt = None

    #-------------------------------------------------------------------------#
    # Scapy methods to relay                                                  #
    #-------------------------------------------------------------------------#

    def show(self, dump=False, indent=3, lvl="", label_lvl=""):
        return self._scapy_pkt.show(dump=dump, indent=indent, lvl=lvl,
                                   label_lvl=label_lvl)

    def show2(self, dump=False, indent=3, lvl="", label_lvl=""):
        return self._scapy_pkt.show2(dump=dump, indent=indent, lvl=lvl,
                                    label_lvl=label_lvl)

    def get_field(self, field:str) -> object:
        return self._scapy_pkt.get_field(field)

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def scapy_pkt(self) -> Packet:
        return self._scapy_pkt
    @scapy_pkt.setter
    def scapy_pkt(self, pkt:Packet) -> None:
        """Set a content to a Packet directly with Scapy format."""
        if isinstance(pkt, Packet):
            self._scapy_pkt = pkt
        else:
            raise BOFProgrammingError("Invalid Scapy Packet ({0})".format(pkt))

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @property
    def fields(self) -> list:
        """Returns the list of fields in packet and subpackets."""
        fieldlist = []
        for item in self:
            if isinstance(item, BOFPacket):
                fieldlist += item.fields
            elif isinstance(item, Field):
                fieldlist.append(item)
        return fieldlist

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def append(self, other:object, autobind:bool=False) -> None:
        """Adds either a BOFPacket, Scapy Packet or Field to current packet.

        :param other: BOFPacket or Scapy Packet or field to append as payload.
        :param autobind: Whether or not unspecified binding found in Scapy
                         implementation are automatically added.
        :raises BOFProgrammingError: if type is not supported.
        """
        if isinstance(other, BOFPacket) or isinstance(other, Packet):
            self._add_payload(other, autobind=autobind)
        elif isinstance(other, Field): # TODO
            raise NotImplementedError("Don't know how to append a field yet.")
        else:
            raise BOFProgrammingError("Unknown type to append ({0})".format(type(other)))

    #-------------------------------------------------------------------------#
    # Protected                                                               #
    #-------------------------------------------------------------------------#

    def _add_payload(self, other:object, autobind:bool=False) -> None:
        """Adds ``other`` Scapy payload to ``scapy_pkt`` attribute.
        Should not be called directly, please call ``append`` instead.

        This method's behavior is similar to the following code::

            self.scapy_pkt = self.scapy_pkt / other

        It adds the following features::

        - Independently add a ``BOFPacket`` or Scapy ``Packet`` as payload to
          current ``BOFPacket``.
        - Create a binding "on the fly" between the packet and it's payload if
          it was not defined in Scapy's implementation.

        :param other: Scapy or BOF packet to add as payload.
        :param autobind: Whether or not unspecified binding found in Scapy
                         implementation are automatically added.

        Example::

            # Adding a Scapy packet as payload to the current scapy_pkt :
            bof_pkt.scapy_pkt = TCP()
            bof_pkt.append(ModbusADURequest())

            # Adding a BOF packet as payload to the current scapy_pkt :
            bof_pkt1.scapy_pkt = TCP()
            bof_pkt2.scapy_pkt = ModbusADURequest()
            bof_pkt1.append(bof_pkt2)

            # Adding an "unexpected" payload with automatic rebinding :
            bof_pkt.append(HTTP())
            bof_pkt.append(TCP(), autobind=True)
        """
        if isinstance(other, BOFPacket):
            other = other.scapy_pkt
        # Gets the last payload of our packet (will be bound to next payload)
        lastlayer = self._scapy_pkt.lastlayer()
        # TODO: Rewrite + Refactor + Test for existing class name
        clone_pkt_class(lastlayer, lastlayer.__class__.__name__
                        + str(randint(1000000, 9999999)))
        # Checks if binding exists between last layer and the other class
        is_binding = any(other.__class__ in b for b in lastlayer.payload_guess)
        if isinstance(other, Packet) and autobind and not is_binding:
            lastlayer.payload_guess.insert(0, ({}, other.__class__))
            # we may also use Scapy builtin bind_layers or pkt.decode_payload_as()
        self._scapy_pkt = self._scapy_pkt / other

    #-------------------------------------------------------------------------#
    # Builtins                                                                #
    #-------------------------------------------------------------------------#

    def __init__(self, _pkt: bytes = None, scapy_pkt: Packet = Packet()):
        self.scapy_pkt = scapy_pkt

    def __bytes__(self):
        return bytes(self._scapy_pkt)

    def __len__(self):
        return len(self._scapy_pkt)

    def __str__(self):
        return str(self._scapy_pkt)

    def __getattr__(self, attr):
        if self._scapy_pkt and hasattr(self._scapy_pkt, attr):
            return getattr(self._scapy_pkt, attr)
        return object.__getattribute__(self, attr)

    def __iter__(self):
        if self._scapy_pkt:
            yield from self._scapy_pkt.fields_desc
        else:
            raise BOFProgrammingError("BOFPacket object is empty!")

###############################################################################
# To refactor (use as classmethod or within class)                            #
###############################################################################

# As classmethod or protected
def clone_pkt_class(packet:Packet, name:str):
    """Replaces the Scapy ``packet`` class by an exact copy.
    This is a trick used when we need to modify a ``Packet`` class attribute
    without affecting all instances of an object.
    For instance, if we change ``fields_desc`` to add a field, all new
    instances will be changed as this is a class attribute.

    :param packet: the Scapy Packet to update
    :param name: the new class name for packet

    Example::

        scapy_pkt1 = SNMP()
        scapy_pkt2 = SNMP()
        clone_pkt_class(scapy_pkt1, "SNMP2")
        scapy_pkt1.fields_desc.append(new_field)

        As a result, scapy_pkt2 won't contain the new field.
    """
    # Checks if a binding exists between packet and its preceding layer
    # (bindings are defined as a list of tuples `layer.payload_guess`)
    in_payload_guess = False
    if packet.underlayer is not None:
        in_payload_guess = any(packet.__class__ in binding \
                               for binding in packet.underlayer.payload_guess)
    # Duplicates our packet class and replaces it by the clone
    class_copy = type(name, (packet.__class__,), {})
    packet.__class__ = class_copy
    # Bindings with the preceding layer must be done again
    if in_payload_guess:
        packet.underlayer.payload_guess.insert(0, ({}, packet.__class__))
        # we may also use Scapy builtin bind_layers or pkt.decode_payload_as()

# TODO: Move to BOFPacket, replace packet with layer name
def add_field(packet:Packet, new_field:Field, value=None) -> None:
    """Adds a new Scapy field at the end of the specified ``packet``.
    As this may change the behavior for all instances of the same object,
    we first replace the class with a new one.

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
    # Replace the class with a new one (with a random name)
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
