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

###############################################################################
# KNX FRAME CONTENT                                                           #
###############################################################################

#-----------------------------------------------------------------------------#
# KNX fields (byte or byte array) representation                              #
#-----------------------------------------------------------------------------#

KNXFIELDSEP = ","

# TODO
class KnxField(BOFField):
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
                      the block. If True, this value is updated when a field
                      in the block changes (except if this field has arg
                      ``fixed_value`` set to True.
    :param subsizes: If the field is in fact a merge of bit fields (a field
                     usually works only with bytes), this parameter states
                     the size in bits of subfields.

    Instantiate::

        KnxField(name="header length", size=1, default="06")

    As we don't know how to handle bit fields that are not at least one
    byte-long, we can create fields that are not complete bytes (ex: 4bits)
    inside a ``KnxField``. For instance, a field of 4bits and one of 12bits
    are merged into one byte field of 2 bytes (16bits).
        
    ``KnxField`` definition in the JSON spec file has the following format
    if such subfields exist::
    
        {"name": "field1, field2", "type": "field", "size": 2, "subsize": "4, 12"}
    
    The new attribute ``subsize`` shall match the field list from name.
    Here, we indicate that the field is divided into 2 bit fields: 
    ``field1`` is 4 bits-long, ``field2`` is 12 bits long. When referring
    to the field from anywhere else in the code, they should be treated as
    independent fields.
    Subfield are referred to as normal properties named ``field1`` and ``field2``
    independently that return values as bit lists.
    A property to refer to the main field, that returns the value of the complete
    byte array, is created with a name such as ``field1_field2``::

        >>> response.body.cemi.field1.value
        [0, 0, 0, 1]
        >>> response.body.cemi.field2.value
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        >>> response.body.cemi.field1_field2.value
        b'\\x10\\x01' # Stands for 0001 0000 0000 0001

    In a ``KnxField``, we then have a ``subfields`` dictionary that contains a
    set of ``KnxSubField`` objects, which is an inner class of ``KnxField``.
    Values are calculated in bits instead of bytes, the translation between bit
    fields and byte array (when they are manipulated in frames.) shall not be
    the problem of the user.

    **KNX Standard v2.1 03_08_02**
    """
    class KnxSubField(object):
        """Special KNX subfield with bit list values instead of bytes."""
        name:str
        size:int
        __value:list
        def __init__(self, name, size, value=0):
            self.name = name
            self.size = size
            self.value = value
        def __str__(self):
            return "<{0}: {1} ({2}b)>".format(self.name, self.value, self.size)
        @property
        def value(self) -> list:
            return self.__value
        @value.setter
        def value(self, i):
            """Change value, so far we only consider big endian."""
            if isinstance(i, list):
                self.__value = i
            else:
                self.__value = byte.int_to_bit_list(i, size=self.size)


    def __init__(self, **kwargs):
        """Initialize the field according to a set of keyword arguments.

        :raises BOFProgrammingError: If the field has subfields but their
                                     definition is invalid (details in
                                     ``__set_subfields``).
        """
        super().__init__(**kwargs)
        # Case field is separate into bitfields (2B split in fields of 4b & 12b)
        if KNXFIELDSEP in self._name:
            self._name = [x.strip() for x in self._name.split(KNXFIELDSEP)] # Now it's a table
            self.__set_subfields(**kwargs)
        if "default" in kwargs:
            self._update_value(kwargs["default"])
        elif "value" in kwargs:
            self._update_value(kwargs["value"])
        else:
            self._update_value(bytes(self._size)) # Empty bytearray

    def __set_subfields(self, **kwargs):
        """If field (byte) contains subfields (bit), we check that the name list
        and the subsizes match and set the value accordingly using bit to byte
        and byte to bit conversion fuctions. We use bit list instead to make it
        easier (for slices). Item stored in subfield dictionary referred to as
        a name which is called from the rest of the code and by the end user as a
        property like any other regular field.

        :param subsize: Size list (in bits), as a string.
        :raises BOFProgrammingError: If subsize is invalid.
        """
        if "subsize" not in kwargs:
            raise BOFProgrammingError("Fields with subfields shall have subsizes ({0})".format(self._name))
        self._bitsizes = [int(x) for x in kwargs["subsize"].split(KNXFIELDSEP)]
        if len(self._bitsizes) != len(self._name):
            raise BOFProgrammingError("Subfield names do not match subsizes ({0}).".format(self._name))
        self._bitfields = {}
        for i in range(len(self._name)):
            self._bitfields[self._name[i]] = KnxField.KnxSubField(name=self._name[i], size=self._bitsizes[i])

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def value(self) -> bytes:
        return super().value
    @value.setter
    def value(self, content) -> None:
        # Check if IPv4:
        if isinstance(content, str):
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
            if not kwargs["type"].upper() in specs.blocktypes.keys():
                raise BOFProgrammingError("Unknown block type ({0})".format(kwargs["type"]))
            self.name = self.name if len(self.name) else kwargs["type"]
            self.append(self.factory(template=specs.blocktypes[kwargs["type"].upper()]))
        elif "cemi" in kwargs:
            if not kwargs["cemi"] in specs.cemis.keys():
                raise BOFProgrammingError("cEMI is unknown ({0})".format(kwargs["cemi"]))
            self.name = self.name if len(self.name) else "cemi"
            self.append(self.factory(template=specs.blocktypes[specs.cemis[kwargs["cemi"]]["type"]]))
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
            block.append(KnxBlock.factory(template=KnxSpec().blocktypes["HPAI"]))
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
            elif template["type"] in specs.blocktypes.keys():
                nestedblock = cls(name=template["name"])
                content = specs.blocktypes[template["type"]]
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

    :param source: Source address of the frame with format tuple 
                   ``(ip:str, port:int)``.
    :param raw: Raw byte array used to build a KnxFrame object.
    :param header: Frame header as a ``KnxBlock`` object.
    :param body: Frame body as a ``KnxBlock`` which can also contain a set
                 of nested ``KnxBlock`` objects.

    Instantiate::

        KnxFrame(type="DESCRIPTION REQUEST")
        KnxFrame(frame=data, source=address)

    **KNX Standard v2.1 03_08_02**
    """
    __source:tuple
    __specs:KnxSpec

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
        :param frame: Raw bytearray used to build a KnxFrame object.
        :param source: Source address of a frame, as a tuple (ip;str, port:int)
                       Only used is param `frame` is set.
        """
        super().__init__()
        # We do not use BOFFrame.append() because we use properties (not attrs)
        self._blocks["header"] = KnxBlock(type="header")
        self._blocks["body"] = KnxBlock(name="body")
        self.__specs = KnxSpec()
        self.__source = kwargs["source"] if "source" in kwargs else ("",0)
        if "type" in kwargs:
            cemi = kwargs["cemi"] if "cemi" in kwargs else None
            optional = kwargs["optional"] if "optional" in kwargs else False
            self.build_from_sid(kwargs["type"], cemi, optional)
            log("Created new frame from service identifier {0}".format(kwargs["type"]))
        elif "frame" in kwargs:
            self.build_from_frame(kwargs["frame"])
            log("Created new frame from byte array {0} (source: {1})".format(kwargs["frame"],
                                                                             self.__source))
        # Update total frame length in header
        self.update()

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    # TODO
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
        # If sid is bytes, replace the id (as bytes) by the service name
        if isinstance(sid, bytes):
            for service in self.__specs.service_identifiers:
                if bytes.fromhex(self.__specs.service_identifiers[service]["id"]) == sid:
                    sid = service
                    break
        # Now check that the service id exists and has an associated body
        if isinstance(sid, str):
            if sid not in self.__specs.bodies:
                # Try with underscores (Ex: DESCRIPTION_REQUEST)
                if sid in [to_property(x) for x in self.__specs.bodies]:
                    for body in self.__specs.bodies:
                        if sid == to_property(body):
                            sid = body
                            break
                else:
                    raise BOFProgrammingError("Service {0} does not exist.".format(sid))
        else:
            raise BOFProgrammingError("Service id should be a string or a bytearray.")
        self._blocks["body"].append(KnxBlock.factory(template=self.__specs.bodies[sid],
                                            cemi=cemi, optional=optional))
        # Add fields names as properties to body :)
        for field in self._blocks["body"].fields:
            self._blocks["body"]._add_property(field.name, field)
            if sid in self.__specs.service_identifiers.keys():
                value = bytes.fromhex(self.__specs.service_identifiers[sid]["id"])
                self._blocks["header"].service_identifier._update_value(value)
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
        # HEADER
        self._blocks["header"] = KnxBlock(type="HEADER", name="header")
        self._blocks["header"].fill(frame[:frame[0]])
        blocklist = None
        for service in self.__specs.service_identifiers:
            attributes = self.__specs.service_identifiers[service]
            if bytes(self._blocks["header"].service_identifier) == bytes.fromhex(attributes["id"]):
                blocklist = self.__specs.bodies[service]
                break
        if not blocklist:
            raise BOFProgrammingError("Unknown service identifier ({0})".format(self._blocks["header"].service_identifier.value))
        # BODY
        cursor = frame[0] # We start at index len(header) (== 6)
        for block in blocklist:
            if cursor >= len(frame):
                break
            # If block is a cemi, we need its type before creating the structure
            cemi = frame[cursor:cursor+1] if block["type"] == "cemi" else None
            if cemi: # We get the name instead of the code
                for cemi_type in self.__specs.cemis:
                    attributes = self.__specs.cemis[cemi_type]
                    if cemi == bytes.fromhex(attributes["id"]):
                        cemi = cemi_type
                        break
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
        for service in self.__specs.service_identifiers:
            attributes = self.__specs.service_identifiers[service]
            if bytes(self._blocks["header"].service_identifier) == bytes.fromhex(attributes["id"]):
                return service
        return str(self._blocks["header"].service_identifier.value)

    @property
    def cemi(self) -> str:
        """Return the type of cemi, if any."""
        if "cemi" in self._blocks["body"].attributes:
            for cemi in self.__specs.cemis:
                if bytes(self._blocks["body"].cemi.message_code) == bytes.fromhex(self.__specs.cemis[cemi]["id"]):
                    return cemi
        return ""
