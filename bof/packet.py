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
from sys import getsizeof
from struct import error as struct_error
from socket import gaierror as socket_gaierror
from ipaddress import ip_address
# Scapy
from typing import Union

from scapy.packet import Packet, RawVal
from scapy.fields import Field, PacketField, IPField, MultipleTypeField
# Internal
from bof import log, BOFProgrammingError

###############################################################################
# Constants                                                             #
###############################################################################


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
    # Builtins                                                                #
    #-------------------------------------------------------------------------#

    def __init__(self, _pkt:bytes=None, scapy_pkt:Packet=None, **kwargs):
        self.scapy_pkt = scapy_pkt if scapy_pkt else Packet()
        self._set_fields(**kwargs)

    def __bytes__(self):
        return bytes(self._scapy_pkt)

    def __len__(self):
        return len(self._scapy_pkt)

    def __str__(self):
        return str(self._scapy_pkt)

    def __iter__(self):
        yield from self.fields

    def __getattr__(self, attr):
        """Return attr corresponding to fields in the Scapy packet first."""
        if self._scapy_pkt and hasattr(self._scapy_pkt, attr):
            return getattr(self._scapy_pkt, attr)
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        """If attribute is a field, set it to the Scapy object with changes.
        Scapy Fields only accept values with the appropriate format, but
        BOF does not care, the end user should be able to set values from
        the type she wants. Therefore, if the type is not matching, we replace
        the field with a RawVal field.
        """
        # We try to set attribute as if it was a field
        if self._scapy_pkt:
            try:
                self._set_fields(**{attr:value})
                return
            except BOFProgrammingError:
                pass
        # If it fails, we set it to current attr
        object.__setattr__(self, attr, value)

    def __getitem__(self, key:str) -> bytes:
        """Access a field as bytes using syntax ``bof_pkt["fieldname"]``."""
        field, value = self._get_field(key)
        item = field.i2m(field, value)
        # We want bytes but i2m might return something else
        if isinstance(item, int):
            item = item.to_bytes(field.sz, byteorder="big")
        return item

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
    def fields(self, start_packet:object=None) -> list:
        """Returns the list of fields in ``BOFPacket``."""
        return [field for field, parent in self._field_generator()]

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def append(self, other:object, autobind:bool=False, packet=None, value=None) -> None:
        """Adds either a BOFPacket, Scapy Packet or Field to current packet.

        :param other: BOFPacket or Scapy Packet or field to append as payload.
        :param autobind: Whether or not unspecified binding found in Scapy
                         implementation are automatically added.
        :param packet: Packet at to append ``other`` to.
        :param value: Value to set to a newly-created field.
        :raises BOFProgrammingError: if type is not supported.
        """
        if isinstance(other, BOFPacket) or isinstance(other, Packet):
            self._add_payload(other, autobind=autobind)
        elif isinstance(other, Field): # TODO
            self._add_field(other, packet=packet, value=value)
        else:
            raise BOFProgrammingError("Unknown type to append ({0})".format(type(other)))

    #-------------------------------------------------------------------------#
    # Protected                                                               #
    #-------------------------------------------------------------------------#

    @staticmethod
    def _clone(packet:Packet, name:str):
        """Replaces the Scapy ``packet`` class by an exact copy.
        This is a trick used when we need to modify a ``Packet`` class attribute
        without affecting all instances of an object.
        For instance, if we change ``fields_desc`` to add a field, all new
        instances will be changed as this is a class attribute.
        
        :param packet: the Scapy Packet to update
        :param name: the new class name for packet
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

    #--- Field management ----------------------------------------------------#

    @staticmethod
    def _create_field(name, value, size=0):
        """Create appropriate Field according to the type of ``value``."""
        try:
            ip_address(value)
            return IPField(name, value)
        except ValueError:
            pass
        # Set default type
        size = max(size, len(value))
        return Field(name, value, fmt="{0}s".format(size))

    def _field_generator(self, start_packet:object=None) -> tuple:
        """Yields fields in packet/subpackets with their closest parent."""
        start_packet = self.scapy_pkt if not start_packet else start_packet
        iterlist = [start_packet] if isinstance(start_packet, PacketField) else \
                   [start_packet, start_packet.payload]
        for packet in iterlist:
            for field in packet.fields_desc:
                if isinstance(field, MultipleTypeField):
                    field = field._find_fld()
                if isinstance(field, PacketField) or isinstance(field, Packet):
                    yield from self._field_generator(getattr(packet, field.name))
                if isinstance(field, Field): # We also yield if PacketField
                    yield field, start_packet

    def _get_field(self, name:str) -> tuple:
        """Extract a field from its name anywhere in a Scapy packet.

        :param name: Name of the field to retrieve.
        :returns: A tuple ``field_object, field_value``.
        :raises BOFProgrammingError: if field does not exist.
        """
        for field, parent in self._field_generator():
            if field.name == name:
                return parent.getfield_and_val(name)
        raise BOFProgrammingError("Field does not exist. ({0})".format(name))

    def _set_fields(self, **attrs):
        """Set values to fields using a list of dict ``{field: value, ...}``.
        In constructor, field values are set AFTER the packet type is defined.

        :param fields: List to use to set values to fields. Each entry is a dict
                       with format ``field_name: value_to_set``.
        """
        for field, parent in self._field_generator():
            if field.name in attrs.keys():
                old_value = getattr(parent, field.name)
                # _, old_value = parent.getfield_and_val(field.name)
                try:
                    setattr(parent, field.name, attrs[field.name])
                    raw(parent) # Checks if current Field accepts this value
                except (struct_error, socket_gaierror, TypeError):
                    # # If type does not match the Field type, we replace the Field
                    new_field = self._create_field(field.name, attrs[field.name], field.sz)
                    self._replace_field_type(parent, field, new_field)
                    setattr(parent, field.name, attrs[field.name])
                attrs.pop(field.name)
        if len(attrs):
            raise BOFProgrammingError("Field does not exist. ({0})".format(list(attrs.keys())[0]))

    def _replace_field_type(self, packet, old_field, new_field):
        """Replace a field in a packet with a field with a different type.
        We first need to clone the packet as ``fields_desc`` is a class attribute.

        :param packet: The packet in which we want to replace a field.
        :param old_field; The field that should be replaced.
        :param new_field: The new field with a different type.
        :raises BOFProgrammingError: if old_field does not exist in Packet.
        """
        new_packet_name = "{0}_{1}_{2}".format(packet.__class__.__name__,
                                               packet.name, new_field.name)
        BOFPacket._clone(packet, new_packet_name)
        for index, field in enumerate(packet.fields_desc):
            if field == old_field:
                new_field.owners = deepcopy(old_field.owners)
                packet.fields_desc[index] = new_field
                packet.fieldtype[old_field.name] = new_field
                return
        raise BOFProgrammingError("No field to replace. ({0})".format(old_field.name))

    def _add_field(self, new_field:Field, packet:Union[str,Packet]=None, value=None) -> None:
        """Adds ``new_field`` at the end of current packet or to ``packet``.
        As this may change the behavior for all instances of the same object,
        we first replace the class with a new one.

        :param new_field: The Scapy Field to add to current packet's or
                          ``packet``'s list of fields.
        :param packet: Packet to change, either referred to directly or by its
                          name. If not set, default higher level packet is used.
        :param value: A value assigned to the new field.

        Example::

            bof_pkt = BOFPacket(scapy_pkt = TCP()/ModbusADURequest())
            new_field = ByteField("new_field", 0x42)

            # Various syntax allow us to add a Scapy Field to the ModbusADURequest
            # (note that _add_field() should not be called by the end-user)
            bof_pkt._add_field(new_field, "ModbusADU")
            bof_pkt._add_field(new_field, bof_pkt.get_layer("ModbusADU")
            bof_pkt._add_field(new_field, bof_pkt.payload)
        """

        # gets the target layer by its name if not specified directly
        if isinstance(packet, str) and self.scapy_pkt.haslayer(packet):
            packet = self.scapy_pkt.getlayer(packet)

        # if no Packet is assigned, gets the higher level packet
        if not isinstance(packet, Packet):
            packet = self._scapy_pkt.lastlayer()

        # we replace the class with a new one to avoid shared instance issues
        # TODO: check if class name exists before assigning a new name
        BOFPacket._clone(packet, packet.__class__.__name__ + str(
            randint(1000000, 9999999)))

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


    #--- Payload management --------------------------------------------------#

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
        BOFPacket._clone(lastlayer, lastlayer.__class__.__name__
                        + str(randint(1000000, 9999999)))
        # Checks if binding exists between last layer and the other class
        is_binding = any(other.__class__ in b for b in lastlayer.payload_guess)
        if isinstance(other, Packet) and autobind and not is_binding:
            lastlayer.payload_guess.insert(0, ({}, other.__class__))
            # we may also use Scapy builtin bind_layers or pkt.decode_payload_as()
        self._scapy_pkt = self._scapy_pkt / other

