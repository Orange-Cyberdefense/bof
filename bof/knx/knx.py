"""
KNXnet/IP connection and frames implementations, implementing ``bof.network``'s
UDP classes.

Network connection
------------------

KNX usually works over UDP, however KNX specification v2.1 state that TCP can
also be used. The communication between BOF and a KNX object still acts like
a TCP-based protocol, as (almost) every request expects a response.

``KnxNet`` class (for establishing and maintaining a connection) is inherited
from the ``UDP`` class from ``bof.network`` submodule and uses most of its
features. Fill free to change the inheritance to TCP, it may work as long as
the ``TCP`` class mostly follows the same structure as ``UDP`` class.

Usage::

    knxnet = knx.KnxNet()
    knxnet.connect("192.168.0.100", 3671)
    datagram = knxnet.receive()
    print(datagram)
    knxnet.disconnect()

KNX frame handling
------------------

A KNX frame (``KnxFrame``) is a byte array divided into a set of structures. A
frame always has the following format:

:Header: Single structure with basic data including the type of message.
:Content: One or more structures, depending on the type of message.

A structure (``KnxStructure``) is a byte array divided into a set of fields
(``KnxField``). A structure has the following data:

:Name: The name of the structure to be able to refer to it (using a property).
:Content: A set of fields and/or a set of sub-structures.

A field (``KnxField``) is a byte or a byte array with:

:Name: The name of the field to refer to it.
:Size: The number of bytes the field takes.
:Content: A byte or a byte array with the actual content.
"""

from enum import Enum
from os import path
from ipaddress import ip_address

from ..network import UDP, UDPStructure, UDPField
from ..base import BOFProgrammingError, load_json, to_property, log
from .. import byte

###############################################################################
# KNX PROTOCOLS AND FRAMES CONSTANTs                                          #
###############################################################################

KNXSPEC = load_json(path.join(path.dirname(path.realpath(__file__)), "knxnet.json"))
MULTICAST_ADDR = "224.0.23.12"
PORT = 3671

#-----------------------------------------------------------------------------#
# KNXNET.JSON section keys                                                    #
#-----------------------------------------------------------------------------#

SIDS = "service identifiers"
STRUCTURES = "structures"
BODIES = "bodies"

###############################################################################
# KNX FRAME CONTENT                                                           #
###############################################################################

#-----------------------------------------------------------------------------#
# KNX fields (byte or byte array) representation                              #
#-----------------------------------------------------------------------------#

class KnxField(UDPField):
    """A ``KnxField`` is a set of raw bytes with a name, a size and a content
    (``value``).

    :param name: Name of the field, to be referred to using a property.
    :param size: Size of the field (number of bytes), from ``UDPField``.
    :param value: Value contained in the field (in bytes), from ``UDPFIield``.
    :param fixed_size: Set to ``True`` if the ``size`` should not be modified
                       automatically when changing the value (``UDPField``).
    :param fixed_value: Set to ``True`` if the ``value`` should not be
                        modified automatically inside the module (``UDPField``).
    :param is_length: This boolean states if the field is the length field of
                      the structure. If True, this value is updated when a field
                      in the structure changes (except if this field has arg
                      ``fixed_value`` set to True.

    **KNX Standard v2.1 03_08_02**
    """
    __name:str
    __is_length:bool

    def __init__(self, **kwargs):
        """Initialize the field according to a set of keyword arguments."""
        super().__init__(**kwargs)
        # Inherited from UDPField
        self._size = int(kwargs["size"]) if "size" in kwargs else self._size
        # KnxField initialization
        self.__name = kwargs["name"].lower() if "name" in kwargs else ""
        self.__is_length = kwargs["is_length"] if "is_length" in kwargs else False
        if "default" in kwargs:
            self._update_value(kwargs["default"])
        elif "value" in kwargs:
            self._update_value(kwargs["value"])
        else:
            self._update_value(bytes(self._size)) # Empty bytearray

    def __len__(self):
        return len(self._value)

    def __bytes__(self):
        return bytes(self._value)

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    def _update_value(self, content) -> None:
        """Change the value according to automated updated from within the code
        si that nothing is changed in ``fixed_value`` is set to True.

        :param content: A byte array, an integer, or an IPv4 string.
        """
        if self.fixed_value:
            log("Tried to modified field {0} but value is fixed.".format(self.__name))
            return
        self.value = content
        self.fixed_value = False # Property changes this value, we switch back

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def name(self) -> str:
        return self.__name
    @name.setter
    def name(self, name:str) -> None:
        if isinstance(name, str):
            self.__name = name.lower()
        else:
            raise BOFProgrammingError("Field name should be a string.")

    @property
    def value(self) -> bytes:
        return self._value
    @value.setter
    def value(self, content) -> None:
        """Set ``content`` to value according to 3 types of data: byte array,
        integer or string representation of an IPv4 address.
        
        Sets ``fixed_value`` to True to avoid rechanging the value automatically
        using length updated.
        """
        if isinstance(content, bytes):
            self._value = byte.resize(content, self.size)
        elif isinstance(content, str):
            # Check if IPv4:
            try:
                ip_address(content)
                self._value = byte.from_ipv4(content)
            except ValueError:
                self._value = bytes.fromhex(content)
                self._value = byte.resize(self._value, self.size)
        elif isinstance(content, int):
            self._value = byte.from_int(content, size=self.size)
        else:
            raise BOFProgrammingError("Field value should be bytes, str or int.")
        self.fixed_value = True

    @property
    def is_length(self) -> bool:
        return self.__is_length
    @is_length.setter
    def is_length(self, value:bool) -> None:
        self.__is_length = value

#-----------------------------------------------------------------------------#
# KNX structures (set of fields) representation                               #
#-----------------------------------------------------------------------------#

class KnxStructure(UDPStructure):
    """A ``KnxStructure`` contains an ordered set of other structures and/or
    an ordered set of fields (``KnxField``) of one or more bytes.

    A structure has the following properties:

    - According to **KNX Standard v2.1 03_08_02**, the first byte of the
      structure should contain the length of the structure.
    - A non-terminal ``KnxStructure`` contains a set of other ``KnxStructure``.
    - A terminal ``KnxStructure`` contains a set of ``KnxField``.
    - A ``KnxStructure`` can also contain a mix of structures and fields.

    :param name: Name of structure, so that it can be accessed by its name
                 using a property.
    :param structure: List of structures, fields or both.
    """
    __name:str
    __structure:list

    def __init__(self, **kwargs):
        """Initialize the ``KnxStructure`` with a mandatory name and optional
        arguments to fill in the structure list (with fields or substructures).

        Available keyword arguments:

        :param name: String to refer to the structure using a property.
        :param type: Type of structure, this part should be used prior to
                     structure object's initialization, i.e. not here.

        Some other keywords arguments depend on the type given (``size``,
        ``dibtype``, ``default``, etc.).
        """
        self.name = kwargs["name"] if "name" in kwargs else ""
        self.__structure = []

    def __bytes__(self):
        raw = b''
        for item in self.__structure:
            raw += bytes(item)
        return raw

    def __len__(self):
        """Return the size of the structure in total number of bytes."""
        return len(bytes(self))

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    @staticmethod
    def factory(structure) -> list:
        """Creates a list of ``KnxStructure``-inherited object according to the
        list of templates specified in parameter ``structure``.

        :param structure: template dictionary or list of template dictionaries
                          for ``KnxStructure`` object instantiation.
        :returns: A list of ``KnxStructure`` object (one by item in ``structure``).
        :raises BOFProgrammingError: If the value of argument "type" in a
                                     structure dictionary is unknown.
        """
        structlist = []
        if isinstance(structure, list):
            for item in structure:
                structlist += KnxStructure.factory(item)
        elif isinstance(structure, dict):
            if not "type" in structure or structure["type"] == "structure":
                structlist.append(KnxStructure(**structure))
            elif structure["type"] == "field":
                structlist.append(KnxField(**structure))
            elif structure["type"] in KNXSPEC[STRUCTURES].keys():
                structlist += KnxStructure.factory(KNXSPEC[STRUCTURES][structure["type"]])
            else:
                raise BOFProgrammingError("Unknown structure type ({0})".format(structure))
        return structlist

    @classmethod
    def build_header(cls) -> object:
        """Creates a KnxStructure with header template and attributes, with no
        argument. You will have to add them later.

        :returns: The instance of a new KnxStructure object.
        """
        header = cls(name="header")
        header.append(cls.factory(KNXSPEC[STRUCTURES]["HEADER"]))
        return header

    def append(self, structure) -> None:
        """Appends a structure, a field of a list of structures and/fields to
        current structure's content. Adds the name of the structure to the list
        of current's structure properties. Ex: if ``structure.name`` is ``foo``,
        it could be referred to as ``self.foo``.

        :param structure: ``KnxStructure``, ``KnxField`` or a list of such objects.
        """
        if isinstance(structure, KnxField) or isinstance(structure, KnxStructure):
            self.__structure.append(structure)
            # Add the name of the structure as a property to this instance
            if len(structure.name) > 0:
                setattr(self, to_property(structure.name), structure)
        elif isinstance(structure, list):
            for item in structure:
                self.append(item)
        self.update()

    def update(self):
        """Update all fields corresponding to structure lengths. Ex: if a
        structure has been modified, the update will change the value of
        the structure length field to match (unless this field's ``fixed_value``
        boolean is set to True.
        """
        for item in self.__structure:
            if isinstance(item, KnxStructure):
                item.update()
            elif isinstance(item, KnxField):
                if item.is_length:
                    item._update_value(len(self))

    def remove(self, name:str) -> None:
        """Remove the field ``name`` from the structure (or substructure).
        If several fields have the same name, only the first one is removed.
        
        :param name: Name of the field to remove.
        :raises BOFProgrammingError: if there is no corresponding field.
        """
        name = name.lower()
        for item in self.__structure:
            if isinstance(item, KnxStructure):
                item.remove()
            elif isinstance(item, KnxField):
                if item.name == name or to_property(item.name) == name:
                    self.__structure.remove(item)
                    delattr(self, to_property(item.name))
                    del(item)
                    break

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name:str):
        if isinstance(name, str):
            self.__name = name.lower()
        else:
            raise BOFProgrammingError("Structure name should be a string.")

    @property
    def fields(self) -> list:
        self.update()
        fieldlist = []
        for item in self.__structure:
            if isinstance(item, KnxStructure):
                fieldlist += item.fields
            elif isinstance(item, KnxField):
                fieldlist.append(item)
        return fieldlist

    @property
    def field_names(self) -> list:
        """Gives the list of attributes added to the structure (field names)."""
        return [x for x in self.__dict__.keys() if not x.startswith("_KnxStructure__")]

#-----------------------------------------------------------------------------#
# KNX frames / datagram representation                                        #
#-----------------------------------------------------------------------------#

class KnxFrame(object):
    """Object representation of a KNX message (frame) with methods to build
    and read KNX datagrams.

    A frame contains a set of byte arrays (structures) so that:

    - It always starts with a header with a defined format.
    - The frame body contains one or more structures and varies according to
      the type of KNX message (defined in header).

    :param source: Source address of the frame with format tuple 
                   ``(ip:str, port:int)``.
    :param raw: Raw byte array used to build a KnxFrame object.
    :param header: Frame header as a ``KnxStructure`` object.
    :param body: Frame body as a ``KnxStructure`` which can also contain a set
                 of other ``KnxStructure`` objects.

    **KNX Standard v2.1 03_08_02**
    """
    __source:tuple
    __header:KnxStructure
    __body:KnxStructure

    def __init__(self, **kwargs):
        """Initialize a KnxFrame object from various origins using values from
        keyword argument (kwargs).

        Available frame initialization methods:
        
        :Empty frame: Using no argument, a user can then define the content of
                      the frame manually (or keep an empty frame).
        :Byte array: Build the object from a raw byte array (e.g. received from
                     a KNX object).
        :Template: Build the object from a template of existing KNX message,
                   using a service identifier (sid). Templates can be found,
                   modified, removed or added in the KNX spec JSON file.

        Keywords arguments:

        :param sid: Service identifier as a string or bytearray (2 bytes),
                    sid is used to build a frame according to the structure
                    template associated to this service identifier.
        :param frame: Raw bytearray used to build a KnxFrame object.
        :param source: Source address of a frame, as a tuple (ip;str, port:int)
                       Only used is param `frame` is set.
        """
        # Empty frame (no parameter)
        self.__source = ("",0)
        self.__header = KnxStructure.build_header()
        self.__body = KnxStructure(name="body")
        # Fill in the frame according to parameters
        if "sid" in kwargs:
            self.build_from_sid(kwargs["sid"])
            log("Created new frame from service identifier {0}".format(kwargs["sid"]))
        elif "frame" in kwargs:
            self.build_from_frame(kwargs["frame"], kwargs["source"])
            log("Created new frame from byte array {0} (source: {1})".format(kwargs["kwargs"],
                                                                             kwargs["source"]))
        # Update total frame length in header
        self.update()

    def __bytes__(self):
        """Overload so that bytes(frame) returns the raw KnxFrame bytearray."""
        self.update()
        return self.raw

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def build_from_sid(self, sid) -> None:
        """Fill in the KnxFrame object according to a predefined frame format
        corresponding to a service identifier. The frame format (structures
        and field) can be found or added in the KNX specification JSON file.

        :param sid: Service identifier as a string (service name) or as a
                    byte array (normally on 2 bytes but, whatever).
        :raises BOFProgrammingError: If the service identifier cannot be found
                                     in given JSON file.
        """
        # If sid is bytes, replace the id (as bytes) by the service name
        if isinstance(sid, bytes):
            for service in KNXSPEC[SIDS]:
                if bytes.fromhex(service["id"]) == sid:
                    sid = service["name"]
                    break
        # Now check that the service id exists and has an associated body
        if isinstance(sid, str):
            if sid not in KNXSPEC[BODIES]:
                raise BOFProgrammingError("Service {0} does not exist.".format(sid))
        else:
            raise BOFProgrammingError("Service id should be a string or a bytearray.")
        self.__body.append(KnxStructure.factory(KNXSPEC[BODIES][sid]))
        # Change header according to sid
        for service in KNXSPEC[SIDS]:
            if service["name"] == sid:
                self.__header.service_identifier._update_value(service["id"])
        self.update()

    def build_from_frame(self, frame:bytes, source:tuple=None) -> None:
        """Fill in the KnxFrame object using a frame as a raw byte array. This
        method is used when receiving and parsing a file from a KNX object.

        :param frame: KNX frame as a byte array (or anything, whatever)
        :param source: If byte array is received from a remote object, source
                       should be the address of that object as a tuple with
                       format ``(ip:str, port:int)``. Else, None.
        """
        raise NotImplementedError("Build from frame.")

    def update(self):
        """Update all fields corresponding to structure lengths. Ex: if a
        structure has been modified, the update will change the value of
        the structure length field to match (unless this field's ``fixed_value``
        boolean is set to True.

        For frames, the ``update()`` methods also update the ``total length``
        field in header, which requires an additional operation.
        """
        self.__body.update()
        self.__header.update()
        if "total_length" in self.__header.field_names:
            self.__header.total_length._update_value(byte.from_int(len(self.__header) + len(self.__body)))

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def header(self):
        """Builds the raw byte set and returns it."""
        self.update()
        return self.__header

    @property
    def body(self):
        """Builds the raw byte set and returns it."""
        self.update()
        return self.__body

    @property
    def raw(self):
        """Builds the raw byte set and returns it."""
        self.update()
        return bytes(self.__header) + bytes(self.__body)

###############################################################################
# KNXNET/IP NETWORK CONNECTION                                                #
###############################################################################

class KnxNet(UDP):
    """KNXnet/IP communication over UDP with protocol KNX.

    - Data transmission details are in **KNX Standard v2.1 - 03_03_04**.
    - Sent and received datagrams are returned as ``KnxFrame`` objects.
    - Relies on ``bof.network.UDP()``.
    - Only ``connect()`` and ``receive()`` are overriden from class ``UDP``.
    """

    #-------------------------------------------------------------------------#
    # Override                                                                #
    #-------------------------------------------------------------------------#

    def connect(self, ip:str, port:int=3671, init:bool=True) -> object:
        """Initialize KNXnet/IP connection over UDP.

        :param ip: IPv4 address as a string with format ("A.B.C.D").
        :param port: Default KNX port is 3671 but can be changed.
        :param init: If set to ``True``, a KNX frame ``DESCRIPTION_REQUEST``
                     is sent when establishing the connection. The other part
                     should reply with a ``DESCRIPTION_RESPONSE`` returned as
                     a ``KnxFrame`` object.
        :returns: A ``KnxFrame`` with the parsed ``DESCRIPTION_RESPONSE`` if
                  any, else returns ``None``.
        """
        super().connect(ip, port)
        if init:
            init_frame = KnxFrame(sid="DESCRIPTION REQUEST")
            init_frame.body.ip_address._update_value(self.source[0])
            init_frame.body.port._update_value(self.source[1])
            return self.send_receive(bytes(init_frame))
        return None

    def receive(self, timeout:float=1.0) -> object:
        """Overrides ``UDP``'s ``receive()`` method so that it returns a parsed
        ``KnxFrame`` object when receiving a datagram instead of raw byte array.

        ;param timeout: Time to wait (in seconds) to receive a frame (default 1s)
        :returns: A parsed KnxFrame with the received frame's representation.
        """
        data, address = super().receive(timeout)
        return KnxFrame(frame=data, source=address)
