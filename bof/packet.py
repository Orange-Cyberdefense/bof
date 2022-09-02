"""Interfaces with a packet as a Scapy object, with specific features.

A BOFPacket is a sort of wrapper around a Scapy Packet object, and
implements specific features or changes relative to Scapy's behavior when
interacting with this packet.

The Scapy Packet is used as a basis for BOF to manipulate frames with its own
syntax. You don't need to know how to use Scapy to use BOF.  However, you can
still perform "Scapy stuff" on the packet by directly accessing
``BOFPacket.scapy_pkt`` attribute.

.. note:: BOFPacket DOES NOT inherit from Scapy packet, because we don't need a
          "specialized" class, but a "translation" from BOF usage to Scapy
          objects.

Example (keep in mind that BOFPacket should not be instantiated directly :))::

    pkt = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())
    print(pkt.scapy_pkt.basic_otter_1_1, pkt.basic_otter_1_1) # Same output
    pkt.basic_otter_1_1 = "192.168.1.2" # Not the expected type, BOF converts it
    pkt.show2()
"""
import gc
from random import randint, choice
from copy import deepcopy
from sys import getsizeof
from struct import error as struct_error
from socket import gaierror as socket_gaierror
from ipaddress import ip_address
from typing import Union
# Scapy
from scapy.compat import raw
from scapy.packet import Packet, RawVal
from scapy.fields import *
# Internal
from bof import log, BOFProgrammingError

###############################################################################
# Constants                                                                   #
###############################################################################

CHANGEABLE_TYPES = (ByteField, ShortField, IntField) # May be completed

###############################################################################
# BOFPacket class                                                             #
###############################################################################

class BOFPacket(object):
    """Base class for BOF network packet handling, to inherit in subclasses.

    This class should not be instantiated directly but protocol-specific
    Packet classes in BOF shall inherit it. It acts as a wrapper around
    Scapy-based packets in the specified protocol, either relaying, replacing
    or modifying Scapy default behaviors on Packets and Fields.

    :param _pkt: Raw Packet bytes used to build a packet (mostly done at
                 reception, but you can manually create a packet from bytes)
    :param scapy_pkt: Actual Scapy ``Packet`` object, used by BOF for protocol
                      implementation-related stuff. Can be referred to directly
                      to do "Scapy stuff" inside BOF.
    :param kwargs: Field values to set when instantiating the class. Format is
                   ``field_name=value, ...``. If two fields have the same name,
                   it sets the first one.

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
        """Returns either a field (final), a scapy_pkt attr or this class' attr.

        For a field to be returned, ``attr`` must be the name of a "terminal"
        field, not of a container for other fields (PacketField or Packet).
        BOF forbids access to fields via absolute path without using the
        ``scapy_pkt`` attribute to avoid confusions when getting/setting values
        to fields.

        If the attribute is not a final field, we return in that order:
        - An attribute with that name in ``scapy_pkt`` (if not a PacketField)
        - The corresponding attribute in the current instance.

        Example::

            bof_pkt.port = 3671 # Works
            bof_pkt.scapy_pkt.control_endpoint.port = 3671 # Works

            bof_pkt.control_endpoint.port = 3671 # Raises exception
        """
        # We try to set attribute as if it was a field
        if self._scapy_pkt:
            try:
                _, value, _ = self._get_field(attr)
                return value
            except BOFProgrammingError:
                # We check if scapy_pkt's corresponding attribute is a
                # PacketField or a Packet. If not, we return this attribute.
                if hasattr(self._scapy_pkt, attr):
                    if attr in [x.name for x in self.fields]:
                        raise BOFProgrammingError("This field cannot be accessed "
                                                  "directly ({0}).".format(attr)) from None
                    return getattr(self._scapy_pkt, attr)
        # If there were no final field nor scapy_pkt attr, we return this object's.
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        """Sets a value to an attribute with changes if the attribute is a field.

        Scapy Fields only accept values with the appropriate format, but BOF
        does not care, the end user should be able to set values from the type
        she wants. Therefore, if the type is not matching, The Field is replaced
        with a Field of the same name and new content, with a different type.
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
        field, ivalue, parent = self._get_field(key)
        mvalue = field.i2m(parent, ivalue)
        if isinstance(mvalue, int):
            mvalue = mvalue.to_bytes(field.sz, byteorder="big")
        return mvalue

    def __setitem__(self, key:str, mvalue:bytes) -> None:
        """Directly set a value as bytes to a field without changing its type.

        Example::

            bof_pkt["fieldname"] = b"\x00"
        """
        field, oldval, parent = self._get_field(key)
        ivalue = field.m2i(parent, mvalue)
        if isinstance(oldval, int) and isinstance(ivalue, bytes):
            ivalue = int.from_bytes(ivalue, byteorder="big")
        setattr(parent, key, ivalue)

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def scapy_pkt(self) -> Packet:
        return self._scapy_pkt
    @scapy_pkt.setter
    def scapy_pkt(self, pkt:Packet) -> None:
        """Set a content to a Packet directly with Scapy format.
        
        :raises BOFProgrammingError: if pkt is not a Scapy Packet object.
        """
        if isinstance(pkt, Packet):
            self._scapy_pkt = pkt
        else:
            raise BOFProgrammingError("Invalid Scapy Packet ({0})".format(pkt))

    @property
    def type(self) -> str:
        """Get information about the packet's type (protocol-dependent).
        
        Should be overriden in subclasses to match a protocol's different
        types of packets. For instance, BOF's packet for the KNX protocol
        (``KNXPacket``) returns the type of packet as a name, relying on its
        identifier fields. If identifier is 0x0203, ``pkt.type`` indicates that
        the packet is a ``DESCRIPTION REQUEST``.
        """
        return self.__class__.__name__

    @property
    def fields(self) -> list:
        """Returns the list of field objects in a ``BOFPacket``.

        Can be used to retrieve the list of fields as a name list with::

            [x.name for x in pkt.fields]
        """
        return [field for field, parent in self._field_generator()]

    @property
    def length(self) -> int:
        """Returns the length of the packet (number of bytes)."""
        return len(self._scapy_pkt)
    
    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def copy(self):
        """Copies the current instance by rebuilding it from its bytes.
        Works appropriately only if the original packet is valid.
        Any attribute not strictly bound to bytes is ignored, you should add it.

        Example::

          copy_of_pkt = self.copy()
          copy_of_pkt.show2() # Should be the same thing as self.show2()
        """
        # return self.__class__(scapy_pkt=self.scapy_pkt.copy())
        return self.__class__(bytes(self))
    
    def get(self, *args) -> object:
        """Get a field either from its name, partial or absolute path.

        Partial indicates part of the absolute path, in other words where the
        search for the field should start from.

        :param args: Can take from one to many arguments. The last argument
                     must be the field you look for. Previous "path" arguments
                     must be in the right order (even if the path is not
                     complete).
        :raises BOFProgrammingError: If field not found or not supported.
        """
        parent = self._scapy_pkt
        for arg in args:
            if arg is args[-1]: # Last item
                field, value, _ = self._get_field(arg, parent, packets=True)
                return field if isinstance(field, PacketField) else value
            else:
                _ , _, parent = self._get_field(arg, parent, packets=True)
        raise BOFProgrammingError("Could not find field ({0}).".format(args))

    def update(self, value:object, *args) -> None:
        """Set value to a field either from its name, partial or absolute path.

        Partial indicates part of the absolute path, in other words where the
        search for the field should start from.

        :param value: The value to set to the field. If the type does not match,
                      the type of field will be changed.
        :param args: Can take from one to many arguments. The last argument
                     must be the field you look for. Previous "path" arguments
                     must be in the right order (even if the path is not
                     complete).
        :raises BOFProgrammingError: If field not found or not supported.
        """
        parent = self._scapy_pkt
        for arg in args:
            if arg is args[-1]: # Last item
                field, _, _ = self._get_field(arg, parent, packets=True)
                self._set_fields(start_packet=parent, **{field.name: value})
                return
            else:
                _ , parent, _ = self._get_field(arg, parent, packets=True)
        raise BOFProgrammingError("Could not find field ({0}).".format(args))

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

    def fuzz(self, iterations:int=0, include:list=None, exclude:list=None):
        """Generator function. Sets a random value to a random field in packet.
        
        :param iterations: Number of packet to create (default is infinite loop)
        :param include: List of field names to include to fuzzing.
        :param exclude: List of field names to exclude from fuzzing.

        Example::

          pkt = KNXPacket(type="configuration request")
          for frame in pkt.fuzz():
            print(frame)
        """
        if include and len(include):
            include = include if isinstance(include, list) else [include]
            fields = [x.name for x in self.fields if x.name in include]
        else:
            exclude = exclude if isinstance(exclude, list) else [exclude]
            fields = [x.name for x in self.fields if x.name not in exclude]
        ct = 0
        # To avoid side effects, we do not use the current instance directly
        packet = self.copy()
        while True:
            try:
                field, old_value, _ = packet._get_field(choice(fields))
            except BOFProgrammingError:
                # Some fields cannot be changed (ex: PacketField)
                continue
            new_value = field.randval()
            packet[field.name] = new_value
            yield packet, field.name, packet[field.name]
            packet[field.name] = old_value
            ct += 1
            if ct == iterations: # Can never be 0 -> infinite loop in that case
                break

    #-------------------------------------------------------------------------#
    # Protected                                                               #
    #-------------------------------------------------------------------------#

    @staticmethod
    def _clone(packet:Packet, name:str) -> None:
        """Replaces the Scapy ``packet`` class by an exact copy.

        This is a trick used when we need to modify a ``Packet`` class attribute
        without affecting all instances of an object.
        For instance, if we change ``fields_desc`` to add a field, all new
        instances will be changed as this is a class attribute.
        
        :param packet: the Scapy Packet to update.
        :param name: the new class name for packet.
        """
        # Checks if a binding exists between packet and its preceding layer
        # (bindings are defined as a list of tuples `layer.payload_guess`)
        in_payload_guess = False
        if packet.underlayer is not None:
            in_payload_guess = any(packet.__class__ in binding \
                                   for binding in packet.underlayer.payload_guess)
        # Duplicates our packet class and replaces it by the clone
        # first checks that provided name is not already used, otherwise generates a new one
        while name in [type(o).__name__ for o in gc.get_objects()]:
            name = name + '_' + str(randint(1000000, 9999999))
        class_copy = type(name, (packet.__class__,), {})
        packet.__class__ = class_copy
        # Bindings with the preceding layer must be done again
        if in_payload_guess:
            packet.underlayer.payload_guess.insert(0, ({}, packet.__class__))
            # we may also use Scapy builtin bind_layers or pkt.decode_payload_as()

    #--- Field management ----------------------------------------------------#

    @staticmethod
    def _create_field(name:str, value:object, size:int=0) -> Field:
        """Create appropriate Field according to the type of ``value``.

        Several specific types must be handled differently. So far only
        IP addresses are supported. Please create an issue  or pull request if
        you miss any other one.
        """
        return Field(name, value, fmt="{0}s".format(size))

    def _field_generator(self, start_packet:object=None, terminal=False) -> tuple:
        """Yields fields in packet/packetfields with their closest parent.

        This is where the worst of Scapy comes to life (and is translated to BOF).
        Brace yourselves, and welcome to hell.
        """
        start_packet = self.scapy_pkt if not start_packet else start_packet
        iterlist = [start_packet] if isinstance(start_packet, PacketField) else \
                   [start_packet, start_packet.payload]
        for packet in iterlist:
            for field in packet.fields_desc:
                if isinstance(field, MultipleTypeField):
                    field = field._find_fld()
                elif isinstance(field, ConditionalField) and field._evalcond(packet):
                    field = field.fld
                if isinstance(field, PacketField) or isinstance(field, Packet):
                    pkt = getattr(packet, field.name)
                    # if pkt = None, next call restarts at start_packet (1st line)
                    # and causes infinite loop, so we replace with empty packet.
                    yield from self._field_generator(pkt if pkt else Packet())
                if isinstance(field, Field):
                    yield field, start_packet # Found the packet
                    
    def _get_field(self, name:str, start_packet:object=None, packets:bool=False) -> tuple:
        """Extract a field from its name anywhere in a Scapy packet.

        :param name: Name of the field to retrieve.
        :param start_packet: Packet to start the search from (Packet or PacketField)
        :param packets: If set to True, will also return PacketField objects.
        :returns: A tuple ``field_object, field_value``.
        :raises BOFProgrammingError: if field does not exist.
        """
        for field, parent in self._field_generator(start_packet):
            if field.name == name:
                try:
                    field_and_val = parent.getfield_and_val(name)
                except ValueError:
                    field_and_val = parent.payload.getfield_and_val(name)
                    # field_and_val = None
                # We do not return packetfields directly because we should not
                # manipulate them outside direct call to Scapy or direct access
                # to the fields they contain.
                if not isinstance(field, PacketField) or packets:
                    # getfield_and_val may not return anything for fields in main packet
                    if not field_and_val and parent == self._scapy_pkt:
                        return field, getattr(parent, name), parent
                    elif field_and_val:
                        return field, field_and_val[1], parent
        raise BOFProgrammingError("Field does not exist. ({0})".format(name))

    def _resize(self, value, size, byteorder="big"):
        """Truncates value to size if value is type int, bytes or str.
        We can probably do better but so far it is enough.
        """
        from_bytes = {
            bytes: lambda x: x,
            int: lambda x: int.from_bytes(x, byteorder=byteorder),
            str: lambda x: x.decode("utf-8")
        }
        to_bytes = {
            bytes: lambda x, l: x,
            int: lambda x, l: x.to_bytes(l, byteorder=byteorder),
            str: lambda x, l: x.encode("utf-8")
        }
        SIZE = {
            bytes: lambda x: len(x),
            int: lambda x: ((x.bit_length() + 7) // 8),
            str: lambda x: len(x)
        }
        T = type(value)
        if T in SIZE and SIZE[T](value) > size:
            bvalue = to_bytes[T](value, SIZE[T](value))
            bvalue = bvalue[len(bvalue)-size:] if byteorder == 'big' else bvalue[:size]
            value = from_bytes[type(value)](bvalue)
        return value

    def _setattr(self, parent, field, value):
        """Set value to field using setattr on parent.
        For some fields, we may need to truncate fields using ``_resize()``.
        """
        if isinstance(field, CHANGEABLE_TYPES) or type(field) == Field:
            value = self._resize(value, field.sz)
        setattr(parent, field.name, value)

    def _any2i(self, parent, field, new_value) -> bool:
        """Try to set a value to a field and see if it passes or not.
        If it fails, the field will be replaced with a field of another type.

        :returns: True if field was set without raising exceptions, False otherwise.
        """
        # Handle special fields
        if isinstance(field, IPField):
            try:
                ip_address(new_value)
            except ValueError:
                return False # We have to change the field's type
        # Try to assign: if it fails, we have to change the field's type as well
        try:
            self._setattr(parent, field, new_value)
            raw(parent)
            return True
        except (ValueError, struct_error):
            pass # Any other exception is unexpected and we let it happen
        return False

    def _set_fields(self, start_packet:object=None, **attrs) -> None:
        """Set values to fields using a list of dict ``{field: value, ...}``.
        In constructor, field values are set AFTER the packet type is defined.

        :param start_packet: Packet or PacketField to start the search from.
        :param fields: List to use to set values to fields. Each entry is a dict
                       with format ``field_name: value_to_set``.
        :raises BOFProgrammingError: if field was not found.
        """
        for field, parent in self._field_generator(start_packet=start_packet):
            if field.name in attrs.keys():
                result = self._any2i(parent, field, attrs[field.name])
                if not result:
                    # # If type does not match the Field type, we replace the Field
                    new_field = self._create_field(field.name, attrs[field.name], field.sz)
                    self._replace_field(parent, field, new_field)
                    self._setattr(parent, field, attrs[field.name])
                attrs.pop(field.name)
        if len(attrs):
            raise BOFProgrammingError("Field does not exist. ({0})".format(list(attrs.keys())[0]))

    ### WIP ###

    def _replace_field(self, packet:Packet, old_field:Field, new_field:Field):
        """Replace a field in a packet with a field with a different type.
        We first need to clone the packet class as ``fields_desc`` is a class
        attribute and will be changed for every instance of that class otherwise.

        :param packet: The packet in which we want to replace a field.
        :param old_field; The field that should be replaced.
        :param new_field: The new field with a different type.
        :raises BOFProgrammingError: if ``old_field`` does not exist in Packet.
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
        # Fets the target layer by its name if not specified directly
        if isinstance(packet, str) and self.scapy_pkt.haslayer(packet):
            packet = self.scapy_pkt.getlayer(packet)
        # If no Packet is assigned, gets the higher level packet
        if not isinstance(packet, Packet):
            packet = self._scapy_pkt.lastlayer()
        # We replace the class with a new one to avoid shared instance issues
        BOFPacket._clone(packet, packet.__class__.__name__)
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
        # Checks if binding exists between last layer and the other class
        is_binding = any(other.__class__ in b for b in lastlayer.payload_guess)
        # TODO: re-initializes payload_class method if it was previously changed ?
        if isinstance(other, Packet) and autobind and not is_binding:
            # clone class because we are going to affect all instances otherwise
            self._clone(lastlayer, lastlayer.__class__.__name__)
            # modifies guess_payload_class function
            lastlayer.__class__.guess_payload_class = Packet.guess_payload_class
            # updates payload_guess list
            lastlayer.payload_guess.insert(0, ({}, other.__class__))
            # we may also use Scapy builtin bind_layers or pkt.decode_payload_as()
        self._scapy_pkt = self._scapy_pkt / other

