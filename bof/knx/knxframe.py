"""
KNX frame handling
------------------

KNXnet/IP frames handling implementation, implementing ``bof.frame``'s
``BOFSpec``, ``BOFFrame``, ``BOFBlock``, ``BOFField`` and ``BOFBitField``
classes.

A KNX frame (``KnxFrame``) is a byte array divided into a set of blocks. A
frame always has the following format:

:Header: Single block with basic data including the type of message.
:Body: One or more blocks, depending on the type of message.

A block (``KnxBlock``) is a byte array divided into a set of fields
(``KnxField``). A block has the following data:

:Name: The name of the block to be able to refer to it (using a property).
:Content: A set of fields and/or nested blocks.

A field (``KnxField``) is a byte or a byte array with:

:Name: The name of the field to refer to it.
:Size: The number of bytes the field takes.
:Content: A byte or a byte array with the actual content.
"""

from os import path
from ipaddress import ip_address
from textwrap import indent

from ..base import BOFProgrammingError, to_property, log
from ..frame import BOFFrame, BOFBlock, BOFField, USER_VALUES, VALUE
from .. import byte, spec

###############################################################################
# KNX-related constants                                                       #
###############################################################################

KNXSPECFILE = "knxnet.json"

TOTAL_LENGTH = "total_length"

###############################################################################
# KNX SPECIFICATION CONTENT                                                   #
###############################################################################


class KnxSpec(spec.BOFSpec):
    """Singleton class for KnxSpec specification content usage.
    Inherits ``BOFSpec``.

    The default specification is ``knxnet.json`` however the end user is free
    to modify this file (add categories, contents and attributes) or create a
    new file following this format.
    """

    def __init__(self, filepath:str=None):
        if not filepath:
            filepath = path.join(path.dirname(path.realpath(__file__)), KNXSPECFILE)
        super().__init__(filepath)

    def get_code_value(self, code:str, identifier) -> str:
        code = self._get_dict_key(self.codes, code)
        if isinstance(identifier, bytes) and code in self.codes:
            for key in self.codes[code]:
                if identifier == bytes.fromhex(key):
                    return self.codes[code][key]
        if isinstance(identifier, str):
            identifier = to_property(identifier)
            for service in self.codes[code].values():
                if identifier == to_property(service):
                    return service
        return None

    def get_code_key(self, dict_key:dict, name:str) -> bytes:
        name = to_property(name)
        dict_key = self._get_dict_key(self.codes, dict_key)
        for key, value in self.codes[dict_key].items():
            if name == to_property(value):
                return bytes.fromhex(key)
        return None

###############################################################################
# KNX FRAME CONTENT                                                           #
###############################################################################

#-----------------------------------------------------------------------------#
# KNX fields (byte or byte array) representation                              #
#-----------------------------------------------------------------------------#

class KnxField(BOFField):
    """A ``KnxField`` is a set of raw bytes with a name, a size and a content
    (``value``). Inherits ``BOFField``.

    Instantiate::

        KnxField(name="header length", size=1, default="06")

    **KNX Standard v2.1 03_08_02**
    """

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def value(self) -> bytes:
        return super().value
    @value.setter
    def value(self, content) -> None:
        if isinstance(content, str):
            # Check if content is an IPv4 address (A.B.C.D):
            try:
                ip_address(content)
                content = byte.from_ipv4(content)
            except ValueError:
                # Check if content is a KNX address (X.Y.Z or X/Y/Z)
                knx_addr = byte.from_knx(content)
                content = knx_addr if knx_addr else content
        super(KnxField, self.__class__).value.fset(self, content)

#-----------------------------------------------------------------------------#
# KNX blocks (set of fields) representation                                   #
#-----------------------------------------------------------------------------#

class KnxBlock(BOFBlock):
    """Object representation of a KNX block. Inherits ``BOFBlock``.

    A KNX block has the following properties:

    - According to **KNX Standard v2.1 03_08_02**, the first byte of the
      block should (but does not always) contain the length of the block.
    - A non-terminal ``KnxBlock`` contains one or more nested ``KnxBlock``.
    - A terminal ``KnxBlock`` only contains a set of ``KnxField``.
    - A ``KnxBlock`` can also contain a mix of blocks and fields.

    Usage example::

        descr_resp = KnxBlock(name="description response")
        descr_resp.append(KnxBlock(type="DIB_DEVICE_INFO"))
        descr_resp.append(KnxBlock(type="DIB_SUPP_SVC_FAMILIES"))
    """

    @classmethod
    def factory(cls, template, **kwargs) -> object:
        """Returns either a KnxBlock or a KnxField, that's why it's a
        factory as a class method.

        :param template: Template of a block or field as a dictionary.
        :returns: A new instance of a KnxBlock or a KnxField.

        Keyword arguments:

        :param user_values: Default values to assign a field as a dictionary
                            with format {"field name": b"value"}
        :param value: Content of block or field to set.
        """
        if spec.TYPE in template and template[spec.TYPE] == spec.FIELD:
            value = b''
            if USER_VALUES in kwargs and template[spec.NAME] in kwargs[USER_VALUES]:
                value = kwargs[USER_VALUES][template[spec.NAME]]
            elif VALUE in kwargs and kwargs[VALUE]:
                if isinstance(template[spec.SIZE], bytes):
                    template[spec.SIZE] = byte.to_int(template[spec.SIZE])
                value = kwargs[VALUE][:template[spec.SIZE]]
            return KnxField(**template, value=value)
        return cls(**template, **kwargs)

    def __init__(self, **kwargs):
        """Initialize the ``KnxBlock`` with a mandatory name and optional
        arguments to fill in the block content list (with fields or nested
        blocks).
        """
        self._spec = KnxSpec()
        super().__init__(**kwargs)

#-----------------------------------------------------------------------------#
# KNX frames / datagram representation                                        #
#-----------------------------------------------------------------------------#

class KnxFrame(BOFFrame):
    """Object representation of a KNX message (frame) with methods to build
    and read KNX datagrams.

    A frame contains a set of byte arrays (blocks) so that:

    - It always starts with a header with a defined format.
    - The frame body contains one or more blocks and varies according to
      the type of KNX message (defined in header).

    :param raw: Raw byte array used to build a KnxFrame object.
    :param header: Frame header as a ``KnxBlock`` object.
    :param body: Frame body as a ``KnxBlock`` which can also contain a set
                 of nested ``KnxBlock`` objects.

    Instantiate::

        KnxFrame(type="DESCRIPTION REQUEST")
        KnxFrame(frame=data, source=address)

    **KNX Standard v2.1 03_08_02**
    """
    _user_args = {
        # {Argument name: field name} 
        "type": "service identifier",
        "cemi": "message code",
        "connection": "cri connection type code"
    }

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

        :param type: Type of the frame (service identifier) as a string or 
                    bytearray (2 bytes), type is used to build a frame
                    according to the blocks template associated to this
                    service identifier.
        :param optional: Boolean, set to True if we want to create a frame with
                         optional fields (from spec).
        :param bytes: Raw bytearray used to build a KnxFrame object.
        :param *: Other params corresponding to default values can be given.
                  The param name must be the name of the field to fill.
        """
        self._spec = KnxSpec()
        super().__init__(KnxBlock, **kwargs)
        self.update()

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def update(self):
        """Update all fields corresponding to block lengths.

        For KNX frames, the ``update()`` methods also update the ``total length``
        field in header, which requires an additional operation.
        """
        super().update()
        if spec.HEADER in self._blocks.keys() and \
           TOTAL_LENGTH in self._blocks[spec.HEADER].attributes:
            total = sum([len(block) for block in self._blocks.values()])
            self._blocks[spec.HEADER].total_length._update_value(byte.from_int(total))

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def header(self):
        self.update()
        return self._blocks[spec.HEADER]
    @property
    def body(self):
        self.update()
        return self._blocks[spec.BODY]

    @property
    def sid(self) -> str:
        """Return the name associated to the frame's service identifier, or
        empty string if it is not set.
        """
        sid = self._spec.get_code_value("service identifier",
                                       self._blocks[spec.HEADER].service_identifier.value)
        return sid if sid else str(self._blocks[spec.HEADER].service_identifier.value)

    @property
    def cemi(self) -> str:
        """Return the type of cemi, if any."""
        return self._spec.get_code_value("message code", self._blocks[spec.BODY].cemi.message_code.value)
