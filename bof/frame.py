"""Global objects from frames representation on different protocols.
Classes in this module should be inherited by protocol implementations.

We assume that a frame has the following structure:

:Frame: The global frame structure as a ``BOFFrame`` object.
:Block: The frame contains one or more blocks as ``BOFBlock`` objects.
:Field: Each block contains one or more fieds (final byte arrays) as
        ``BOFField`` objects.
:BitField: A field can be divided into subfields which are not on entire
           bytes (ex: 4 bits long or 12 bit long). They are reprensented
           as ``BOFBitField`` objects within a field.
"""

from textwrap import indent

from .base import BOFProgrammingError, to_property, log
from . import byte, spec

###############################################################################
# Bit field representation within a field                                     #
###############################################################################

class BOFBitField(object):
    """As we don't know how to handle bit fields that are not at least one
    byte-long, we create fields that are not complete bytes (ex: 4bits)
    inside a ``BOFField``, represented as ``BOFBitField`` objects.

    For instance, a field of 4bits and one of 12bits are merged into one byte
    field of 2 bytes (16bits).

    The use of bit fields involves changes to the definition of fields in a
    JSON specification file. The name field is divided into a list, and the
    keyword ``bitsizes`` is introduced.::
    
        {"name": "field1, field2", "type": "field", "size": 2, "bitsizes": "4, 12"}

    The attribute ``bitsizes`` shall match the field list from ``name``.
    Here, we indicate that the field is divided into 2 bit fields: 
    ``field1`` is 4 bits-long, ``field2`` is 12 bits long. When referring
    to the field from anywhere else in the code, they should be treated as
    independent fields.

    The use of BOFBitFields instead of BOFField should not be seen by the
    end-user: Bit fields are referred to as normal properties named ``field1``
    and ``field2``, independent, that return values as bit lists.

    In a ``BOFField``, we then have a ``bitfields`` list that contains a
    set of ``BOFBitField`` objects. The ``BOFField`` object has name
    ``["field1", "field2"]`` (name is a list, that's how we know it has bit
    fields). A property to refer to the main field, that returns the value of the
    complete byte array, is created with a name such as ``field1_field2``.

    Finally, values are calculated in bits instead of bytes, the translation
    between bit fields and byte array (when they are manipulated in frames)
    shall not be the problem of the enduser::

        >>> response.body.cemi.field1.value
        [0, 0, 0, 1]
        >>> response.body.cemi.field2.value
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        >>> response.body.cemi.field1_field2.value
        b'\\x10\\x01' # Stands for 0001 0000 0000 0001
    """
    name:str
    size:int
    __value:list # Bit list

    def __init__(self, name:str, size:int, value=0):
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


###############################################################################
# Field representation within a block                                         #
###############################################################################

class BOFField(object):
    """Object representation of a field within a block inside a frame. A field
    is a set of raw bytes with (at least) a name, a size and a value.

    :param name: Name of the field. Is used to refer to the field and to create
                 an attribute in parent block.
    :param size: Length of the field (in number of bytes)
    :param value: Value stored in a field (in bytes)
    :param is_length: Boolean stating if the field is a length. If ``True`` and
                      ``fixed_value`` is False, the value is updated when a
                      field in the parent block is changed and the block length
                      changes.
    :param fixed_size: If ``size`` is modified by the end-user, this parameter
                       is set to ``True`` to prevent methods from automatically
                       updating it (manual mode).
    :param fixed_value: If ``value`` is modified by the end-user, this parameter
                        is set to ``True`` to prevent methods from automatically
                        updating it (manual mode).
    :param bitfields: Some field are not on one byte, and the best solution we
                      found is to store bit fields within byte fields... This
                      parameter should contain a list of ``BOFBitField`` objects
                      or None.
    :param bitsizes: List storing the sizes (in bit) of bit fields within the
                     field.
    """
    _name:str
    _size:int
    _value:bytes
    _is_length:bool
    _fixed_size:bool
    _fixed_value:bool
    _bitfields:list
    _bitsizes:list

    def __init__(self, **kwargs):
        self.name = kwargs["name"] if "name" in kwargs else ""
        self._value = kwargs["value"] if "value" in kwargs else b''
        self._size = int(kwargs["size"]) if "size" in kwargs else max(1, byte.get_size(self._value))
        self._is_length = kwargs["is_length"] if "is_length" in kwargs else False
        self._fixed_size = kwargs["fixed_size"] if "fixed_size" in kwargs else False
        self._fixed_value = kwargs["fixed_value"] if "fixed_value" in kwargs else False
        self._set_bitfields(**kwargs)
        # From now on, _update_value must be used to modify values within the code
        if "value" in kwargs:
            self._update_value(kwargs["value"])
        elif "default" in kwargs:
            self._update_value(kwargs["default"])
        else:
            self._update_value(bytes(self._size))

    def _set_bitfields(self, **kwargs):
        """If the field contains bitfields (name has format ``name1, ``name2``
        and JSON definition of field contains ``bitsizes``, we set the 
        attributes for bit field management accordingly (list of bit fields and
        size of each bit field.
        """
        self._bitfields = None
        self._bitsizes = None
        if not spec.SEPARATOR in self._name:
            return
        if "bitsizes" not in kwargs:
            raise BOFProgrammingError("Fields with bit fields shall have bitsizes ({0}).".format(self._name))
        self._name = [x.strip() for x in self._name.split(spec.SEPARATOR)] # Now it's a table
        self._bitsizes = [int(x) for x in kwargs["bitsizes"].split(spec.SEPARATOR)]
        if len(self._bitsizes) != len(self._name):
            raise BOFProgrammingError("Bitfield names do not match bitsizes ({0}).".format(self._name))
        self._bitfields = {}
        for i in range(len(self._name)):
            self._bitfields[self._name[i]] = BOFBitField(name=self._name[i], size=self._bitsizes[i])

    def __str__(self):
        return "<{0}: {1} ({2}B)>".format(self._name, self.value, self.size)

    def __len__(self):
        return len(self.value)

    def __bytes__(self):
        return bytes(self.value)

    def __iter__(self):
        for i in range(len(self.value)):
            yield byte.from_int(self.value[i])

    #-------------------------------------------------------------------------#
    # Internal (should not be used by end users)                              #
    #-------------------------------------------------------------------------#

    def _update_value(self, content) -> None:
        """Use this method to update a value within the code, so that nothing
        is changed if ``fixed_value`` is set to True.

        :param content: The content to set as a value..
        """
        if self._fixed_value:
            log("Tried to modified field {0} but value is fixed.".format(self._name))
            return
        self.value = content
        self._fixed_value = False # The property changes this value, we switch back

    #--------------------------------------------------------------------------#
    # Properties                                                               #
    #--------------------------------------------------------------------------#

    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def name(self, name:str) -> None:
        if isinstance(name, str):
            self._name = name.lower()
        else:
            raise BOFProgrammingError("Field name should be a string.")

    @property
    def size(self) -> int:
        return self._size
    @size.setter
    def size(self, size:int):
        self._size = size
        self._value = byte.resize(self._value, self._size)

    @property
    def value(self) -> bytes:
        if self._bitfields:
            bit_list = []
            for bitfield in self._bitfields.values():
                bit_list += bitfield.value
            return byte.from_bit_list(bit_list)
        else:
            return self._value
    @value.setter
    def value(self, content) -> None:
        if isinstance(content, bytes):
            self._value = byte.resize(content, self.size)
        elif isinstance(content, int):
            self._value = byte.from_int(content, size=self.size)
        elif isinstance(content, str) and content.isdigit():
            self._value = bytes.fromhex(content)
            self._value = byte.resize(self._value, self.size)
        elif isinstance(content, str):
            self._value = content.encode('utf-8')
        else:
            raise BOFProgrammingError("Field value should be bytes, str or int.")
        # Bitfield management
        if self._bitfields:
            bit_list = byte.to_bit_list(self._value, size=sum(self._bitsizes))
            cursor = 0
            for bitfield in self._bitfields.values():
                bitfield.value = bit_list[cursor:cursor+bitfield.size]
                cursor += bitfield.size
        self._fixed_value = True

    @property
    def is_length(self) -> bool:
        return self._is_length
    @is_length.setter
    def is_length(self, value:bool) -> None:
        self._is_length = value

    @property
    def bitfield(self) -> dict:
        return self._bitfields

###############################################################################
# Block representation within a frame                                         #
###############################################################################

class BOFBlock(object):
    """A ``BOFBlock`` object represents a block (set of fields) within a
    frame. It contains an ordered set of nested blocks and/or fields
    (``BOFField``).

    Implementations should inherit this class for block management inside
    frames.

    :param name: Name of the block, so that it can be referred to by its name.
                 It is also use to create an attribute in the parent block.
    :param parent: Parent frame, used when a field or a block depends on the
                   value of a field previously written to the frame.
    :param content: List of blocks, fields or both.
    """
    _name:str
    _content:list
    _parent:object
    _spec:object

    def __init__(self, **kwargs):
        self.name = kwargs["name"] if "name" in kwargs else ""
        self._parent = kwargs["parent"] if "parent" in kwargs else None
        self._content = []

    def __bytes__(self):
        return b''.join(bytes(item) for item in self._content)

    def __len__(self):
        return len(bytes(self))

    def __str__(self):
        ret = ["{0}: {1}".format(self.__class__.__name__, self._name)]
        for item in self._content:
            ret += [indent(str(item), "    ")]
        return "\n".join(ret)

    def __iter__(self):
        yield from self.fields

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def append(self, content) -> None:
        """Appends a block, a field or a list of blocks and/fields to
        current block's content. Adds the name of the block to the list
        of current's block properties. Ex: if ``block.name`` is ``foo``,
        it could be referred to as ``self.foo``.

        :param block: ``BOFBlock``, ``BOFField`` or a list of such objects.

        Example::

            block = KnxBlock(name="atoll")
            block.append(KnxField(name="pom"))
            block.append(KnxBlock(name="galli"))
        """
        if isinstance(content, BOFField) or isinstance(content, BOFBlock):
            self._content.append(content)
            # Add the name of the block as a property to this instance
            if isinstance(content.name, list):
                for bitfield_name in content.name:
                    setattr(self, to_property(bitfield_name), content.bitfield[bitfield_name])
                setattr(self, to_property(" ".join(content.name)), content)
            elif len(content.name) > 0:
                setattr(self, to_property(content.name), content)
        elif isinstance(content, list):
            for item in content:
                self.append(item)
        self.update()

    def update(self):
        """Update all fields corresponding to lengths. Ex: if a block has been
        modified, the update will change the value of the block length field
        to match (unless this field's ``fixed_value`` boolean is set to True.

        Example::

            header.service_identifier.value = b"\x01\x02\x03"
            header.update()
            print(header.header_length.value)
        """
        for item in self._content:
            if isinstance(item, BOFBlock):
                item.update()
            elif isinstance(item, BOFField):
                if item.is_length:
                    item._update_value(len(self))

    def remove(self, name:str) -> None:
        """Remove the field ``name`` from the block (or nested block).
        If several fields have the same name, only the first one is removed.
        
        :param name: Name of the field to remove.
        :raises BOFProgrammingError: if there is no corresponding field.

        Example::

            body = knx.KnxBlock()
            body.append(knx.KnxField(name="abitbol", size=30, value="monde de merde"))
            body.append(knx.KnxField(name="francky", size=30, value="cest oit"))
            body.remove("abitbol")
            print([x.name for x in body.fields])
        """
        name = name.lower()
        for item in self._content:
            if isinstance(item, BOFBlock):
                delattr(self, to_property(name))
                item.remove(name)
            elif isinstance(item, BOFField):
                if item.name == name or to_property(item.name) == name:
                    self._content.remove(item)
                    delattr(self, to_property(name))
                    del(item)
                    break

    #-------------------------------------------------------------------------#
    # Internal (should not be used by end users)                              #
    #-------------------------------------------------------------------------#

    def _add_property(self, name, pointer:object) -> None:
        """Add a property to the object using ``setattr``, should not be used
        outside module.

        :param name: Property name (string or list if field has bit fields)
        :param pointer: The object the property refers to.
        """
        if isinstance(name, list):
            for bitfield_name in name:
                setattr(self, to_property(bitfield_name), pointer.bitfield[bitfield_name])
        elif len(name) > 0:
            setattr(self, to_property(name), pointer)

    def _get_depends_block(self, field:str):
        """If the format of a block depends on the value of a field set
        previously, we look for it and choose the appropriate format.
        The closest field with such name is used.

        :param name: Name of the field to look for and extract value.
        """
        field = to_property(field)
        field_list = list(self._parent)
        field_list.reverse()
        for frame_field in field_list:
            if field == to_property(frame_field.name):
                block = self._spec.get_code_name(frame_field.name, frame_field.value)
                return block
        raise BOFProgrammingError("Field does not exist ({0}).".format(field))

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def name(self, name:str):
        if isinstance(name, str):
            self._name = name.lower()
        else:
            raise BOFProgrammingError("Block name should be a string.")

    @property
    def fields(self) -> list:
        self.update()
        fieldlist = []
        for item in self._content:
            if isinstance(item, BOFBlock):
                fieldlist += item.fields
            elif isinstance(item, BOFField):
                fieldlist.append(item)
        return fieldlist

    @property
    def attributes(self) -> list:
        """Gives the list of attributes added to the block (field names)."""
        self.update()
        return [x for x in self.__dict__.keys() if not x.startswith("_")]

    @property
    def content(self) -> list:
        return self._content

###############################################################################
# Network frames / datagram representation                                    #
###############################################################################

class BOFFrame(object):
    """Object representation of a protocol-independent network frame. Protocol
    implementations with the following properties should inherit this class from
    frame representation;
    - The frame is sent and receive as a byte array
    - The frame contains a set of blocks
    - The order of blocks is defined, blocks are named.

    :param blocks: A dictionary containing blocks.

    .. warning: We rely on Python 3.6+'s ordering by insertion. If you use an
                older implementation of Python, blocks may not come in the
                right order (and I don't think BOF would work anyway).
    """
    _blocks:dict

    def __init__(self):
        self._blocks = {}

    def __bytes__(self):
        self.update()
        return self.raw

    def __len__(self):
        self.update()
        return len(self.raw)

    def __iter__(self):
        yield from self.fields

    def __str__(self):
        display = ["{0} object: {1}".format(self.__class__.__name__, repr(self))]
        for block in self._blocks:
            display += ["[{0}]".format(block.upper())]
            for attr in self._blocks[block].content:
                display += [indent(str(attr), "    ")]
        return "\n".join(display)

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def append(self, name, block) -> None:
        """Appends a block to the list of blocks. Creates an attribute with
        the same name in the class.

        :param name: Name of the block to append.
        :param block: Block, must inherit from ``BOFBlock``.
        :raises BOFProgrammingError: If block is not a subclass of
                                     ``BOFBlock``.
        """
        if not isinstance(block, BOFBlock):
            raise BOFProgrammingError("Frame can only contain BOF blocks.")
        self._blocks[name] = block
        setattr(self, to_property(name), self._blocks[name])

    def remove(self, name:str) -> None:
        """Remove a block or feld according to its name from the frame.

        If several fields share the same name, only the first one is removed.

        :param name: Name of the field to remove.
        :raises BOFprogrammingError: if there is no field with such name.

        Example::

            frame.remove("control_endpoint")
            print([x for x in frame.attributes])
        """
        name = name.lower()
        for block in self._blocks.values():
            for item in block.attributes:
                if item == to_property(name):
                    item = getattr(block, item)
                    if isinstance(item, BOFBlock):
                        for field in item.fields:
                            item.remove(to_property(field.name))
                            delattr(block, to_property(field.name))
                        delattr(block, to_property(name))
                        del item

    def update(self) -> None:
        """Automatically update all fields corresponding to block lengths
        (Key ``is_length: True`` in the JSON file and/or attribute
        ``is_length`` == ``True`` in a ``BOFField`` object).

        If a block has been modified and its size has changed, we need the
        total block length field (a lot of protocol use such fields) to match.
        If the ``BOFField`` has the attribute ``fixed_value`` set to ``True``
        (it usually happens when the value of this field has been changed
        manually), then the value is not updated automatically.
        """
        for block in self._blocks.values():
            block.update()

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def raw(self) -> bytes:
        """Builds the raw byte array by combining all blocks in frame."""
        self.update()
        return b''.join([bytes(block) for block in self._blocks.values()])

    @property
    def fields(self) -> list:
        """Returns the content of the frame as a list of final fields."""
        self.update()
        return sum([block.fields for block in self._blocks.values()], [])

    @property
    def attributes(self) -> list:
        """Returns the name of the fields contained in the frame."""
        self.update()
        return sum([block.attributes for block in self._blocks.values()], [])
