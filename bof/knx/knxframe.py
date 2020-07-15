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
        :param frame: Raw bytearray used to build a KnxFrame object.
        """
        super().__init__()
        # We do not use BOFFrame.append() because we use properties (not attrs)
        specs = KnxSpec()
        self._blocks["header"] = KnxBlock(type="header")
        self._blocks["body"] = KnxBlock(name="body")
        if "type" in kwargs:
            cemi = kwargs["cemi"] if "cemi" in kwargs else None
            optional = kwargs["optional"] if "optional" in kwargs else False
            self.build_from_sid(kwargs["type"], cemi, optional)
            log("Created new frame from service identifier {0}".format(kwargs["type"]))
        elif "frame" in kwargs:
            self.build_from_frame(kwargs["frame"])
            log("Created new frame from byte array {0}.".format(kwargs["frame"]))
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
        specs = KnxSpec()
        if isinstance(sid, bytes):
            for service in specs.service_identifiers:
                if bytes.fromhex(specs.service_identifiers[service]["id"]) == sid:
                    sid = service
                    break
        # Now check that the service id exists and has an associated body
        if isinstance(sid, str):
            if sid not in specs.bodies:
                # Try with underscores (Ex: DESCRIPTION_REQUEST)
                if sid in [to_property(x) for x in specs.bodies]:
                    for body in specs.bodies:
                        if sid == to_property(body):
                            sid = body
                            break
                else:
                    raise BOFProgrammingError("Service {0} does not exist.".format(sid))
        else:
            raise BOFProgrammingError("Service id should be a string or a bytearray.")
        self._blocks["body"].append(KnxBlock.factory(template=specs.bodies[sid],
                                            cemi=cemi, optional=optional))
        # Add fields names as properties to body :)
        for field in self._blocks["body"].fields:
            self._blocks["body"]._add_property(field.name, field)
            if sid in specs.service_identifiers.keys():
                value = bytes.fromhex(specs.service_identifiers[sid]["id"])
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
        specs = KnxSpec()
        # HEADER
        self._blocks["header"] = KnxBlock(type="HEADER", name="header")
        self._blocks["header"].fill(frame[:frame[0]])
        blocklist = None
        for service in specs.service_identifiers:
            attributes = specs.service_identifiers[service]
            if bytes(self._blocks["header"].service_identifier) == bytes.fromhex(attributes["id"]):
                blocklist = specs.bodies[service]
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
                for cemi_type in specs.cemis:
                    attributes = specs.cemis[cemi_type]
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
        specs = KnxSpec()
        for service in specs.service_identifiers:
            attributes = specs.service_identifiers[service]
            if bytes(self._blocks["header"].service_identifier) == bytes.fromhex(attributes["id"]):
                return service
        return str(self._blocks["header"].service_identifier.value)

    @property
    def cemi(self) -> str:
        """Return the type of cemi, if any."""
        specs = KnxSpec()
        if "cemi" in self._blocks["body"].attributes:
            for cemi in specs.cemis:
                if bytes(self._blocks["body"].cemi.message_code) == bytes.fromhex(specs.cemis[cemi]["id"]):
                    return cemi
        return ""
