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

    def get_service_id(self, name:str) -> bytes:
        """Returns the content of parameter ``id`` for a given service
        identifier name in KNX spec JSON file.
        """
        value = self.__get_dict_value(self.service_identifiers, name)
        return bytes.fromhex(value["id"]) if value else None

    def get_service_name(self, sid:bytes) -> str:
        """Returns the name of the service identifier with id ``sid``."""
        if isinstance(sid, bytes):
            return self.__get_dict_key(self.service_identifiers, "id", sid)
        if isinstance(sid, str):
            sid = to_property(sid)
            for service in self.service_identifiers:
                if sid == to_property(service):
                    return service
        return None

    def get_body_template(self, name:str) -> list:
        """Returns a template associated to a body, as a list, or None."""
        return self.__get_dict_value(self.bodies, name)

    def get_cemi_name(self, cid:bytes) -> str:
        """Returns the name of the cemi withid ``cid``."""
        if isinstance(cid, bytes):
            return self.__get_dict_key(self.cemis, "id", cid)
        return None

    #-------------------------------------------------------------------------#
    # Internals                                                               #
    #-------------------------------------------------------------------------#

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

    def __get_dict_key(self, dictionary:dict, inner_key:str, value:object) -> str:
        """Return the key associated to a value from a given dictionary inside a
        dictionary. Must be called inside class only.
        """
        for entry in dictionary:
            if bytes.fromhex(dictionary[entry][inner_key]) == value:
                return entry
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

    # TODO
    def __init__(self, **kwargs):
        """Initialize the ``KnxBlock`` with a mandatory name and optional
        arguments to fill in the block content list (with fields or nested
        blocks).

        A ``KnxBlock`` can be pre-filled according to a type or to a cEMI
        block as defined in the specification file.

        Available keyword arguments:

        :param name: String to refer to the block using a property.
        :param type: Type of block. Cannot be used with ``cemi``.
        :param cemi: Type of block if this is a cemi structure. Cannot be used
                     with ``type``.
        """
        super().__init__(**kwargs)
        specs = KnxSpec()
        if "type" in kwargs:
            if not kwargs["type"].upper() in specs.blocks.keys():
                raise BOFProgrammingError("Unknown block type ({0})".format(kwargs["type"]))
            self.name = self.name if len(self.name) else kwargs["type"]
            self.append(self.factory(template=specs.blocks[kwargs["type"].upper()]))
        elif "cemi" in kwargs:
            if not kwargs["cemi"] in specs.cemis.keys():
                raise BOFProgrammingError("cEMI is unknown ({0})".format(kwargs["cemi"]))
            self.name = self.name if len(self.name) else "cemi"
            self.append(self.factory(template=specs.blocks[specs.cemis[kwargs["cemi"]]["type"]]))
            self.message_code.value = bytes.fromhex(specs.cemis[kwargs["cemi"]]["id"])

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    # TODO
    @classmethod
    def factory(cls, **kwargs) -> object:
        """Factory method to create a list of ``KnxBlock`` according to kwargs.
        Available keywords arguments: 
        
        :param template: Cannot be used with ``type``. 
        :param type: Type of block. Cannot be used with ``cemi``.
        :param cemi: Type of block if this is a cemi structure. Cannot be used
                     with ``type``.
        :returns: A list of ``KnxBlock`` objects. 
        
        """
        
        if "template" in kwargs:
            cemi = kwargs["cemi"] if "cemi" in kwargs else None
            optional = kwargs["optional"] if "optional" in kwargs else False
            return cls.create_from_template(kwargs["template"], cemi, optional)
        if "type" in kwargs:
            return cls(type=kwargs["type"], name=name)
        if "cemi" in kwargs:
            optional = kwargs["optional"] if "optional" in kwargs else False
            return cls(cemi=kwargs["cemi"], name="cEMI")
        return None

    # TODO
    @classmethod
    def create_from_template(cls, template, cemi:str=None, optional:bool=False) -> list:
        """Creates a list of ``KnxBlock``-inherited object according to the
        list of templates specified in parameter ``template``.

        :param template: template dictionary or list of template dictionaries
                         for ``KnxBlock`` object instantiation.
        :param cemi: when a block is a cEMI, we need to know what type of
                     cEMI it is to build it accordingly.
        :param optional: build optional templates (default: no/False)
        :returns: A list of ``KnxBlock`` objects (one by item in ``template``).
        :raises BOFProgrammingError: If the value of argument "type" in a
                                     template dictionary is unknown.

        Example::

            block = KnxBlock(name="new block")
            block.append(KnxBlock.factory(template=KnxSpec().blocks["HPAI"]))
        """
        blocklist = []
        specs = KnxSpec()
        if isinstance(template, list):
            for item in template:
                blocklist += cls.create_from_template(item, cemi, optional)
        elif isinstance(template, dict):
            if "optional" in template.keys() and template["optional"] == True and not optional:
                return blocklist
            if not "type" in template or template["type"] == "block":
                blocklist.append(cls(**template))
            elif template["type"] == "field":
                blocklist.append(KnxField(**template))
            elif template["type"] == "cemi":
                blocklist.append(cls(cemi=cemi))
            elif template["type"] in specs.blocks.keys():
                nestedblock = cls(name=template["name"])
                content = specs.blocks[template["type"]]
                nestedblock.append(cls.create_from_template(content, cemi, optional))
                blocklist.append(nestedblock)
            else:
                raise BOFProgrammingError("Unknown block type ({0})".format(template))
        return blocklist

    # TODO
    def fill(self, frame:bytes) -> bytes:
        """Fills in the fields in object with the content of the frame.

        The frame is read byte by byte and used to fill the field in ``fields()``
        order according to each field's size. Hopefully, the frame is the same
        size as what is expected for the format of this block.
        
        :param frame: A raw byte array corresponding to part of a KNX frame.
        :returns: The remainder of the frame (if any) or 0
        """
        cursor = 0
        for field in self.fields:
            field.value = frame[cursor:cursor+field.size]
            cursor += field.size
        if frame[cursor:len(frame)] and self.fields[-1].size == 0: # Varying size
            self.fields[-1].size = len(frame) - cursor
            self.fields[-1].value = frame[cursor:cursor+field.size]

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
        super().__init__()
        self._blocks["header"] = KnxBlock(type="header")
        self._blocks["body"] = KnxBlock(name="body")
        if "type" in kwargs:
            cemi = kwargs["cemi"] if "cemi" in kwargs else None
            optional = kwargs["optional"] if "optional" in kwargs else False
            self.build_from_sid(kwargs["type"], cemi, optional)
            log("Created new frame from service identifier {0}".format(kwargs["type"]))
        elif "bytes" in kwargs:
            self.build_from_frame(kwargs["bytes"])
            log("Created new frame from byte array {0}.".format(kwargs["bytes"]))
        # Update total frame length in header
        self.update()

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def build_from_sid(self, sid, cemi:str=None, optional:bool=False) -> None:
        """Fill in the KnxFrame object according to a predefined frame format
        corresponding to a service identifier. The frame format (blocks
        and field) can be found or added in the KNX specification JSON file.

        :param sid: Service identifier as a string (service name) or as a
                    byte array (normally on 2 bytes but, whatever).
        :param cemi: Type of cEMI if the blocks associated to ``sid`` have
                     a cEMI field/structure.
        :param optional: Boolean, set to True if we want to build the optional
                         blocks/fields as stated in the specs.
        :raises BOFProgrammingError: If the service identifier cannot be found
                                     in given JSON file.

        Example::

            frame = KnxFrame()
            frame.build_from_sid("DESCRIPTION REQUEST")
        """
        if not isinstance(sid, bytes) and not isinstance(sid, str):
            raise BOFProgrammingError("Service id should be a string or a bytearray.")
        spec = KnxSpec()
        # Get data associated service identifier
        sid = spec.get_service_name(sid)
        if not sid or sid not in spec.bodies:
            raise BOFProgrammingError("Service {0} does not exist.".format(sid))
        template = spec.get_body_template(sid)
        # Create KnxBlock according to template
        self._blocks["body"].append(KnxBlock.factory(
            template=template, cemi=cemi, optional=optional))
        # Add fields names as properties to body :)
        for field in self._blocks["body"].fields:
            self._blocks["body"]._add_property(field.name, field)
        # Update header
        self._blocks["header"].service_identifier._update_value(spec.get_service_id(sid))
        self.update()

    # TODO
    def build_from_frame(self, frame:bytes) -> None:
        """Fill in the KnxFrame object using a frame as a raw byte array. This
        method is used when receiving and parsing a file from a KNX object.

        The parsing relies on the block lengths sometimes stated in first byte
        of each part (block) of the frame.

        :param frame: KNX frame as a byte array (or anything, whatever)

        Example::

            data, address = knx_connection.receive()
            frame = KnxFrame(frame=data, source=address)

        """
        spec = KnxSpec()
        # Fill in the header and retrieve information about the frame.
        header_length = frame[0]
        self._blocks["header"].fill(frame[:header_length]) # TODO
        sid = spec.get_service_name(self._blocks["header"].service_identifier.value)
        template = spec.get_body_template(sid)
        if not template:
            raise BOFProgrammingError("Unknown service identifier ({0})".format(sid))
        # BODY
        cursor = frame[0] # We start at index len(header) (== 6)
        for block in template:
            if cursor >= len(frame):
                break
            # If block is a cemi, we need its type before creating the structure
            cemi = spec.get_cemi_name(frame[cursor:cursor+1]) if block["type"] == "cemi" else None
            # factory returns a list but we only expect one item
            block_object = KnxBlock.factory(template=block,cemi=cemi)[0]
            if isinstance(block_object, KnxField):
                block_object.value = frame[cursor:cursor+block_object.size]
                cursor += block_object.size
            else:
                block_object.fill(frame[cursor:cursor+frame[cursor]])
                cursor += frame[cursor]
            self._blocks["body"].append(block_object)

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
        sid = KnxSpec().get_service_name(self._blocks["header"].service_identifier.value)
        return sid if sid else str(self._blocks["header"].service_identifier.value)

    @property
    def cemi(self) -> str:
        """Return the type of cemi, if any."""
        KnxSpec().get_cemi_name(self._blocks["body"].cemi.message_code)
