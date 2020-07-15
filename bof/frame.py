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

from .base import BOFProgrammingError, to_property

###############################################################################
# Bit field representation within a field                                     #
###############################################################################

class BOFBitField(object):
    pass

###############################################################################
# Field representation within a block                                         #
###############################################################################

class BOFField(object):
    pass

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
    :param content: List of blocks, fields or both.
    """
    _name:str
    _content:list

    def __init__(self, **kwargs):
        self.name = kwargs["name"] if "name" in kwargs else ""
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
                for subname in content.name:
                    setattr(self, to_property(subname), content.subfield[subname])
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

        :param name: Property name (string or list if field has subfields)
        :param pointer: The object the property refers to.
        """
        if isinstance(name, list):
            for subname in name:
                setattr(self, to_property(subname), pointer.subfield[subname])
        elif len(name) > 0:
            setattr(self, to_property(name), pointer)

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
