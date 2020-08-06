"""
OPC UA frame handling
------------------

OPC UA frames handling implementation, implementing ``bof.frame``'s
``BOFSpec``, ``BOFFrame``, ``BOFBlock`` and ``BOFField`` classes.
See `bof/frame.py`.

BOF should not contain code that is bound to a specific version of a protocol's
specifications. Therefore OPC UA frame structure and its content is described in
:file:`opcua.json`.
"""

from os import path

from ..base import BOFProgrammingError, to_property, log
from ..frame import BOFFrame, BOFBlock, BOFField, USER_VALUES, VALUE
from .. import byte, spec

###############################################################################
# OPCUA SPECIFICATION CONTENT                                                 #
###############################################################################

OPCUASPECFILE = "opcua.json"

class OpcuaSpec(spec.BOFSpec):
    """Singleton class for OPC UA specification content usage.
    Inherits ``BOFSpec``, see `bof/frame.py`.

    The default specification is ``opcua.json`` however the end user is free
    to modify this file (add categories, contents and attributes) or create a
    new file following this format.

    Usage example::

        spec = opcua.OpcuaSpec()
        block_template = spec.get_block_template("HEL_BODY")
        item_template = spec.get_item_template("HEL_BODY", "protocol version")
        message_structure = spec.get_code_value("message_type", "HEL")
    """

    def __init__(self):
        """Initialize the specification object with a JSON file.
        If `filepath` is not specified, we use a default one specified in 
        `OPCUASPECFILE`.
        """
        #TODO: add support for custom file path (depends on BOFSpec)
        filepath = path.join(path.dirname(path.realpath(__file__)), OPCUASPECFILE)
        super().__init__(filepath)

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def get_item_template(self, block_name:str, item_name:str) -> dict:
        """Returns an item template (dict of values) from a `block_name` and
        a `field_name`.
        
        Note that an item template can represent either a field or a block,
        depending on the "type" key of the item.

        :param block_name: Name of the block containing the item.
        :param item_name: Name of the item to look for in the block.
        :returns: Item template associated to block_name and item_name
        """
        if block_name in self.blocks:
            for item in self.blocks[block_name]:
                if item['name'] == item_name:
                    return item
        return None
    
    def get_block_template(self, block_name:str) -> list:
        """Returns a block template (list of item templates) from a block name.

        :param block_name: Name of the block we want the template from.
        :returns: Block template associated with the specifified block_name.
        """
        return self._get_dict_value(self.blocks, block_name) if block_name else None
    
    def get_code_value(self, code:str, identifier) -> str:
        """Returns the value associated to an `identifier` inside a
        `code` association table. See opcua.json + usage
        example to better understand the association table concept.
        
        :param identifier: Key we want the value from, as str or byte.
        :param code: Association table name we want to look into
                                 for identifier match.
        :returns: value associated to an identifier inside a code.
        """
        code = self._get_dict_key(self.codes, code)
        if isinstance(identifier, bytes) and code in self.codes:
            for key in self.codes[code]:
                if identifier == str.encode(key):
                    return self.codes[code][key]
        elif isinstance(identifier, str) and code in self.codes:
            for key in self.codes[code]:
                if identifier == key:
                    return self.codes[code][key]
        return None

    def get_code_key(self, dict_key:dict, name:str) -> bytes:
        return name

###############################################################################
# OPC UA FRAME CONTENT                                                        #
###############################################################################

#-----------------------------------------------------------------------------#
# OPC UA fields (byte or byte array) representation                           #
#-----------------------------------------------------------------------------#

class OpcuaField(BOFField):
    """An ``OpcuaField`` is a set of raw bytes with a name, a size and a
    content (``value``). Inherits ``BOFField``, see `bof/frame.py`.

    Usage example::

        # creating a field from parameters
        field = opcua.OpcuaField(name="protocol version", value=b"1", size=4)

        # creating a field from a template
        item_template_field = spec.get_item_template("HEL_BODY", "protocol version")
        field = opcua.OpcuaField(**item_template_field)

        # editing field value
        field.value = b'\x00\x00\x00\x02'
    """

    # For now there is no need to redefine getter and setter property from
    # BOFField (base class attributes are compatible with OPC UA field spec)

#-----------------------------------------------------------------------------#
# OPC UA blocks (set of fields) representation                                #
#-----------------------------------------------------------------------------#

class OpcuaBlock(BOFBlock):
    """Object representation of an OPC UA block. Inherits ``BOFBlock``. 
    See `bof/frame.py`.

    An OpcuaBlock (as well as a BOFBlock) contains a set of items.
    Those items can be fields as well as blocks, therefore creating
    so-called "nested blocks" (or "sub-block").

    A block is usually built from a template which gives its structure.
    Bytes can also be specified to "fill" this block stucture. If the bytes
    values are coherent, the structure can also be determined directly from
    them.
    If no structure is specified the block remains empty.

    Some block field value (typically a sub-block type) may depend on the
    value of another field. In that case the keyword "depends:" is used to
    associate the variable to its value, based on given parameters to another
    field. The process can be looked in details in the `__init__` method, and
    understood from examples.

    Usage example:: 

        # empty block creation
        block = opcua.OpcuaBlock(name="empty_block")

        # block creation with direct parameters
        block = opcua.OpcuaBlock(name="header", type="HEADER")

        # block creation from an item template (as found in json spec file)
        item_template_block = {"name": "header", "type": "HEADER"}
        block = opcua.OpcuaBlock(**item_template_block)

        # fills block with byte value at creation
        (note that here a type is still mandatory)
        block = opcua.OpcuaBlock(type="STRING", value=14*b"\x01")

        # a block with dependency can be created from raw bytes (no default parameter)
        data1 = b'HEL\x00...'
        data2 = b'\x00...'
        block = opcua.OpcuaBlock()
        block.append(opcua.OpcuaBlock(value=data1, parent=block, 
                        **{"name": "header", "type": "HEADER"}))
        block.append(opcua.OpcuaBlock(alue=data2, parent=block, 
                        **{"name": "body", "type": "depends:message_type"}))
        # this in an example of block looking in its sibling for dependency value

        # we can access a list of available block `fields` using :
        block.attributes

        # and access one of those `fields` with :
        block.field_name
    """

    @classmethod
    def factory(cls, item_template:dict, **kwargs) -> object:
        """Returns either an `OpcuaBlock` or an `OpcuaField` depending on the
        template specified item type. That's why it's a factory as a class method.

        :param item_template: item template representing sub-block or field.
        :returns: A new instance of an OpcuaBlock or an OpcuaField.
        
        Keyword arguments:
        
        :param user_values: Default values to assign a field as dictionnary.
        :param value: Bytes value to fill the item (block or field) with.
        """
        # case where item template represents a field (non-recursive)
        if spec.TYPE in item_template and item_template[spec.TYPE] == spec.FIELD:
            value = b''
            if USER_VALUES in kwargs and item_template[spec.NAME] in kwargs[USER_VALUES]:
                value = kwargs[USER_VALUES][item_template[spec.NAME]]
            elif VALUE in kwargs and kwargs[VALUE]:
                value = kwargs[VALUE][:item_template[spec.SIZE]]
            return OpcuaField(**item_template, value=value)
        # case where item template represents a sub-block (nested/recursive block)
        else:
            return cls(**item_template, **kwargs)
    
    def __init__(self, **kwargs):
        """Initialize the ``OpcuaBlock``.

            Keyword arguments:

            :param type: a string specifying block type (as found in json
                         specifications) to construct the block on.
            :param user_values: default values to assign a field as dictionnary
                         (can therefore be used to construct blocks with
                         dependencies if not found in raw bytes, see example
                         above)
            :param value: bytes value to fill the block with
                         (can create dependencies on its own, see example
                         above). If user_values parameter is found it overcomes
                         the value passed as bytes.

            See example in class docstring to understand dependency creation
            either with user_values or value parameter.
            
        """
        self._spec = OpcuaSpec()
        super().__init__(**kwargs)

#-----------------------------------------------------------------------------#
# OPC UA frames representation                                                #
#-----------------------------------------------------------------------------#

class OpcuaFrame(BOFFrame):
    """Object representation of an OPC UA frame, created from the template
    in `opcua.json`.

    Uses various initialization methods to create a frame :

        :Byte array: Build the object from a raw byte array, typically used
                        when receiving incoming connection. In this case block
                        dependencies are identified automatically.
        :Keyword arguments: Uses keyword described in __user_values to fill frame
                            fields.

    Usage example::

        # creation from raw bytes (format is automatically identified)
        data = b'HEL\x00..'
        frame = opcua.OpcuaFrame(bytes=data)
        
        # creation from known type (who is actually a needed dependence)
        # in order to create the frame (see frame structure in opcua.json)
        frame = opcua.OpcuaFrame(type="HEL")
    """

    _user_args = {
        # {Argument name: field name} 
        "type": "message_type",
    }

    def __init__(self, **kwargs):
        """Initialize an OpcuaFrame from various origins using values from
        keyword arguments :
        
        :param byte: raw byte array used to build a frame.
        :param user_values: every element of __default specifies arguments
                            that can be passed in order to set fields values
                            at frame creation.
        """
        self._spec = OpcuaSpec()
        super().__init__(OpcuaBlock, **kwargs)
        self.update()

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def update(self):
        """Update ``message_size`` field in header according to total
        frame length.
        """
        #super().update()
        if "message_size" in self._blocks[spec.HEADER].attributes:
            total = sum([len(block) for block in self._blocks.values()])
            self._blocks[spec.HEADER].message_size._update_value(byte.from_int(total))

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
