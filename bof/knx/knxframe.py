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
from ..frame import BOFFrame, BOFBlock, BOFField, BOFBitField
from ..spec import BOFSpec
from .. import byte

###############################################################################
# KNX SPECIFICATION CONTENT                                                   #
###############################################################################

KNXSPECFILE = "knxnet.json"

class KnxSpec(BOFSpec):
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

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def get_block_template(self, name:str) -> list:
        """Returns a template associated to a body, as a list, or None."""
        return self.__get_dict_value(self.blocks, name) if name else None

    def get_code_name(self, dict_key:str, identifier) -> str:
        dict_key = self.__get_dict_key(self.codes, dict_key)
        if isinstance(identifier, bytes):
            for key in self.codes[dict_key]:
                if identifier == bytes.fromhex(key):
                    return self.codes[dict_key][key]
        if isinstance(identifier, str):
            identifier = to_property(identifier)
            for service in self.codes["service identifier"].values():
                if identifier == to_property(service):
                    return service
        return None

    def get_code_id(self, dict_key:dict, name:str) -> bytes:
        name = to_property(name)
        for key, value in self.codes[dict_key].items():
            if name == to_property(value):
                return bytes.fromhex(key)
        return None

    #-------------------------------------------------------------------------#
    # Internals                                                               #
    #-------------------------------------------------------------------------#

    def __get_dict_key(self, dictionary:dict, dict_key:str) -> str:
        """As a key can be given with wrong formatting (underscores,
        capital, lower, upper cases, we match the value given with
        the actual key in the dictionary.
        """
        dict_key = to_property(dict_key)
        for key in dictionary:
            if to_property(key) == dict_key:
                return key

    def __get_dict_value(self, dictionary:dict, key:str) -> object:
        """Return the value associated to a key from a given dictionary. Key
        is insensitive, the value can have different types. Must be called
        inside class only.
        """
        key = to_property(key)
        for entry in dictionary:
            if to_property(entry) == key:
                return dictionary[entry]
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
                pass
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
        ;returns: A new instance of a KnxBlock or a KnxField.

        Keyword arguments:

        :param defaults: Default values to assign a field as a dictionary
                         with format {"field name": b"value"}
        :param value: Content of block or field to set.
        """
        if "type" in template and template["type"] == "field":
            value = b''
            if "defaults" in kwargs and template["name"] in kwargs["defaults"]:
                value = kwargs["defaults"][template["name"]]
            elif "value" in kwargs and kwargs["value"]:
                value = kwargs["value"][:template["size"]]
            return KnxField(**template, value=value)
        return cls(**template, **kwargs)

    def __init__(self, **kwargs):
        """Initialize the ``KnxBlock`` with a mandatory name and optional
        arguments to fill in the block content list (with fields or nested
        blocks).
        """
        self._spec = KnxSpec()
        super().__init__(**kwargs)
        # Without a type, the block remains empty
        if not "type" in kwargs or kwargs["type"] == "block":
            return
        # Now we extract the final type of block from the arguments
        value = kwargs["value"] if "value" in kwargs else None
        defaults = kwargs["defaults"] if "defaults" in kwargs else {}
        block_type = kwargs["type"]
        if block_type.startswith("depends:"):
            field_name = to_property(block_type.split(":")[1])
            block_type = self._get_depends_block(field_name, defaults)
            if not block_type:
                raise BOFProgrammingError("Association not found for field {0}".format(field_name))
        # We extract the block's content according to its type
        template = self._spec.get_block_template(block_type)
        if not template:
            raise BOFProgrammingError("Unknown block type ({0})".format(block_type))
        # And we fill the block according to its content
        template = [template] if not isinstance(template, list) else template
        for item in template:
            new_item = self.factory(item, value=value,
                                    defaults=defaults, parent=self)
            self.append(new_item)
            # Update value
            if value:
                if len(new_item) >= len(value):
                    break
                value = value[len(new_item):]

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
    __defaults = {
        # {Argument name: field name} 
        "type": "service identifier",
        "cemi": "message code",
        "connection": "connection type code"
    }

    # TODO
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
        """
        spec = KnxSpec()
        super().__init__()
        # We store some values before starting building the frame
        value = kwargs["bytes"] if "bytes" in kwargs else None
        defaults = {}
        for arg, code in self.__defaults.items():
            if arg in kwargs:
                defaults[code] = spec.get_code_id(code, kwargs[arg])
        # Now we can start
        for block in spec.frame:
            # Create block
            self._blocks[block["name"]] = KnxBlock(
                 value=value, defaults=defaults, parent=self, **block)
            # Add fields as attributes to current frame block
            for field in self._blocks[block["name"]].fields:
                self._blocks[block["name"]]._add_property(field.name, field)
            # If a value is used to fill the blocks, update it:
            if value:
                if len(self._blocks[block["name"]]) >= len(value):
                    break
                value = value[len(self._blocks[block["name"]]):]
        # Update total frame length in header
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
        if "total_length" in self._blocks["header"].attributes:
            total = sum([len(block) for block in self._blocks.values()])
            self._blocks["header"].total_length._update_value(byte.from_int(total))

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def header(self):
        self.update()
        return self._blocks["header"]
    @property
    def body(self):
        self.update()
        return self._blocks["body"]

    @property
    def sid(self) -> str:
        """Return the name associated to the frame's service identifier, or
        empty string if it is not set.
        """
        sid = KnxSpec().get_code_name("service identifier",
                                      self._blocks["header"].service_identifier.value)
        return sid if sid else str(self._blocks["header"].service_identifier.value)

    @property
    def cemi(self) -> str:
        """Return the type of cemi, if any."""
        KnxSpec().get_cemi_name(self._blocks["body"].cemi.message_code)
