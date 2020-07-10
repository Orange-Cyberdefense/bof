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

class BOFBitField(object):
    pass

class BOFField(object):
    pass

class BOFBlock(object):
    pass

#-----------------------------------------------------------------------------#
# Network frames / datagram representation                                    #
#-----------------------------------------------------------------------------#

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
