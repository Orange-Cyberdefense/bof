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

from ..network import UDP, UDPStructure, UDPField
from ..base import BOFProgrammingError, load_json, to_property

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

    **KNX Standard v2.1 03_08_02**
    """
    __name:str

    def __init__(self, **kwargs):
        """Initialize the field according to a set of keyword arguments."""
        self._size = int(kwargs["size"]) if "size" in kwargs else 1
        self.__name = kwargs["name"].lower() if "name" in kwargs else ""
        if "default" in kwargs:
            self.value = kwargs["default"]
        elif "value" in kwargs:
            self.value = kwargs["value"]
        else:
            self.value = bytes(self._size) # Empty bytearray

    def __bytes__(self):
        return bytes(self._value)

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
        if isinstance(content, bytes):
            self._value = content
        elif isinstance(content, str):
            self._value = bytes.fromhex(content)
        elif isinstance(content, int):
            self._value = byte.from_int(content)
        else:
            raise BOFProgrammingError("Field value should be bytes, str or int.")


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
        fieldlist = []
        for item in self.__structure:
            if isinstance(item, KnxStructure):
                fieldlist += item.fields
            elif isinstance(item, KnxField):
                fieldlist.append(item)
        return fieldlist

class KnxHPAI(KnxStructure):
    """TODO"""
    pass

class KnxDIB(KnxStructure):
    """TODO"""
    pass

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
        self.__header = KnxStructure(name="header")
        self.__header.append(KnxStructure.factory(KNXSPEC[STRUCTURES]["HEADER"]))
        self.__body = KnxStructure(name="body")
        # Fill in the frame according to parameters
        if "sid" in kwargs:
            self.build_from_sid(kwargs["sid"])
        elif "frame" in kwargs:
            self.build_from_frame(kwargs["frame"], kwargs["source"])

    def __bytes__(self):
        """Overload so that bytes(frame) returns the raw KnxFrame bytearray."""
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

    def build_from_frame(self, frame:bytes, source:tuple=None) -> None:
        """Fill in the KnxFrame object using a frame as a raw byte array. This
        method is used when receiving and parsing a file from a KNX object.

        :param frame: KNX frame as a byte array (or anything, whatever)
        :param source: If byte array is received from a remote object, source
                       should be the address of that object as a tuple with
                       format ``(ip:str, port:int)``. Else, None.
        """
        raise NotImplementedError("Build from frame.")

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def header(self):
        """Builds the raw byte set and returns it."""
        return self.__header

    @property
    def body(self):
        """Builds the raw byte set and returns it."""
        return self.__body

    @property
    def raw(self):
        """Builds the raw byte set and returns it."""
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
            return self.send_receive(bytes(KnxFrame(sid="DESCRIPTION REQUEST")))
        return None

    def receive(self, timeout:float=1.0) -> object:
        """Overrides ``UDP``'s ``receive()`` method so that it returns a parsed
        ``KnxFrame`` object when receiving a datagram instead of raw byte array.

        ;param timeout: Time to wait (in seconds) to receive a frame (default 1s)
        :returns: A parsed KnxFrame with the received frame's representation.
        """
        data, address = super().receive(timeout)
        return KnxFrame(frame=data, source=address)
