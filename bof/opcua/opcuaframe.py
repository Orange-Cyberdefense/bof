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
from ..frame import BOFFrame, BOFBlock, BOFField
from ..spec import BOFSpec

###############################################################################
# OPCUA SPECIFICATION CONTENT                                                 #
###############################################################################

OPCUASPECFILE = "opcua.json"

class OpcuaSpec(BOFSpec):
    """Singleton class for OPC UA specification content usage.
    Inherits ``BOFSpec``, see `bof/frame.py`.

    The default specification is ``opcua.json`` however the end user is free
    to modify this file (add categories, contents and attributes) or create a
    new file following this format.

    Usage example::

        spec = OpcuaSpec()
        block_template = spec.get_block_template(block_name="HEL_BODY")
        item_template = spec.get_item_template("HEL_BODY", "protocol version")
        message_structure = spec.get_association("message_type", "HEL")
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
        """
        if block_name in self.blocks:
            for item in self.blocks[block_name]:
                if item['name'] == item_name:
                    return item
        return None

    def get_block_template(self, block_name:str) -> list:
        """Returns a block template (list of item templates) from a block name.

        :param block_name: Name of the block we want the template from.
        """
        return self._get_dict_value(self.blocks, block_name) if block_name else None
            
    def get_association(self, code_name:str, identifier) -> str:
        """Returns the value associated to an `identifier` inside a `code_name`
        association table. See `opcua.json` + usage example to better 
        understand the association table concept.
        
        :param identifier: Key we want the value from.
        :code name: Association table name we want to look into for identifier
                    match.
        """
        #TODO: add support for bytes codes names (if needed in the specs ?)
        if code_name in self.codes:
            for association in self.codes[code_name]:
                if identifier == association:
                    return self.codes[code_name][association]
        return None
