"""unittest for ``bof.opcua``.

- OPC UA specification gathering
"""

import unittest
from bof import opcua, BOFLibraryError, BOFProgrammingError

class Test01OpcuaSpec(unittest.TestCase):
    """Test class for specification class building from JSON file.
    TODO: Some tests are generic to BOFSpec and could be moved.
    """
    def test_01_opcua_spec_instantiate_default(self):
        """Test that the current `opcua.json` default file is valid."""
        try:
            spec = opcua.OpcuaSpec()
        except BOFLibraryError:
            self.fail("Default opcua.json should not raise BOFLibraryError.")
    def test_02_opcua_spec_instantiate_custom_valid_json(self):
        """Test that a custom and valid opcua spec file works as expected."""
        try:
            spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        except BOFLibraryError:
            self.fail("Valid json spec should not raise BOFLibraryError.")
    def test_03_opcua_spec_instantiate_custom_invalid_json(self):
        """Test that a custom and invalid opcua spec raises exception."""
        with self.assertRaises(BOFLibraryError):
            spec = opcua.OpcuaSpec("./jsons/invalid.json")
    def test_04_opcua_spec_instantiate_custom_invalid_path(self):
        """Test an invalid custom path raises exception."""
        with self.assertRaises(BOFLibraryError):
            spec = opcua.OpcuaSpec("./jsons/unexisting.json")
    def test_05_opcua_spec_property_access_valid():
        """Test that a JSON element can be accessed as property"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        frame_template = spec.frame
        self.assertEqual(frame_template[0]["name"], "header")
    def test_05_opcua_spec_property_access_invalid():
        """Test that a unexisting JSON element can't be accessed as property"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        with self.assertRaises(AttributeError):
            frame_template = spec.unexisting
    def test_06_opcua_spec_get_blocks_valid():
        """Test that we can get block from spec as expected"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        block_template = spec.get_block_template(block_name="HEADER")
        self.assertEqual(block_template[0]["name"], "message_type")
    def test_07_opcua_spec_get_blocks_invalid():
        """Test that an invalid block request returns None"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        block_template = spec.get_block_template(block_name="INVALID")
        self.assertEqual(block_template, None)
    def test_08_opcua_spec_get_item_valid():
        """Test that we can get an item from spec as expected"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        item_template = spec.get_template("HEL_BODY", "protocol_version")
        self.assertEqual(item_template["name"], "protocol_version")
    def test_09_opcua_spec_get_item_invalid():
        """Test that an invalid item request returns None"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        item_template = spec.get_template("INVALID", "INVALID")
        self.assertEqual(item_template, None)
    def test_10_get_association_valid():
        """Test that a valid association is returned as expeted"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        message_structure = spec.get_association("message_type", "HEL")
        self.assertEqual(message_structure, "HEL_BODY")
    def test_11_get_association_invalid():
        """Test that an ivalid association returns None"""
        spec = opcua.OpcuaSpec("./jsons/valid_opcua.json")
        message_structure = spec.get_association("INVALID", "INVALID")
        self.assertEqual(message_structure, None)

class Test02OpcuaField(unittest.TestCase):
    """Test class for field crafting and access.
    Note that we don't test for the whole BOFField behavior, but
    uniquely what we are using in OpcuaField.
    TODO: Some tests are generic to BOFField and could be moved.
    """
    def test_01_opcua_create_field_manual(self):
        """Test that we can craft a field by hand and content is set"""
        field = opcua.OpcuaField(name="protocol_version")
        self.assertEqual(field.name, "protocol_version")
    def test_02_opcua_create_field_template(self):
        """Test that we can craft a field from a template and content is set"""
        spec = opcua.OpcuaSpec()
        item_template_field = spec.get_item_template("HEL_BODY", "protocol_version")
        field = opcua.OpcuaField(**item_template_field)
        self.assertEqual(field.name, "protocol_version")
    def test_03_opcua_field_set(self):
        """Test that a field value can get set as expected."""
        field = opcua.OpcuaField(name="protocol_version", size=4)
        field.value = b'\x00\x00\x00\x01'
        self.assertEqual(field.value, b'\x00\x00\x00\x01')
    def test_04_opcua_field_set_large(self):
        """Test that if we set a value that is to large, it will be cropped."""
        field = opcua.OpcuaField(name="protocol_version", size=4)
        field.value = b'\x00\x00\x00\x00\x01'
        self.assertEqual(field.value, b'\x00\x00\x00\x01')
    def test_05_opcua_field_set_small(self):
        """Test that if we set a value that is to small, it will be extended."""
        field = opcua.OpcuaField(name="protocol_version", size=4)
        field.value = b'\x00\x00\x01'
        self.assertEqual(field.value, b'\x00\x00\x00\x01')

class Test03OpcuaBlock(unittest.TestCase):
    """Test class for block crafting and access."""
    def test_01_opcua_create_block_empty(self):
        """Tests that an empty block can be created and returns an empty list of fields"""
        block = opcua.OpcuaBlock()
        self.assertEqual(block.content, [])
    def test_02_opcua_create_block_template(self):
        """Tests that a block can be created as expected from a template"""
        item_template_block = {"name": "header", "type": "HEADER"}
        block = opcua.OpcuaBlock(item_template_block=item_template_block)
        self.assertEqual(block.content[0].name, "message_type")
    def test_03_opcua_create_block_template_invalid(self):
        """Tests that block creation with invalid template fail case is handled"""
        with self.assertRaises(BOFProgrammingError):
            item_template_block = {"name": "header", "type": "unknown"}
            block = opcua.OpcuaBlock(item_template_block=item_template_block)
    def test_04_opcua_create_block_type(self):
        """Tests that a block can be created as expected from a type name"""
        block = opcua.OpcuaBlock(type="HEADER")
        self.assertEqual(block.content[0].name, "message_type")
    def test_05_opcua_create_block_type_invalid(self):
        """Tests that block creation with invalid type name fail case is handled"""
        with self.assertRaises(BOFProgrammingError):
            block = opcua.OpcuaBlock(type="unknown")
    def test_06_opcua_create_mixed(self):
        """Tests that in case of mixed block type specification
        (type + template) only the type is kept"""
        item_template_block = {"name": "header", "type": "unknown"}
        block = opcua.OpcuaBlock(item_template_block=item_template_block, type="STRING")
        self.assertEqual(block.content[0].name, "string_length")
        self.assertNotEqual(block.content[0].name, "message_type")
    def test_07_opcua_create_nested_block(self):
        """Test for manual creation of nested block"""
        block = opcua.OpcuaBlock(type="HEADER")
        sub_block = opcua.OpcuaBlock(type="STRING")
        block.append(sub_block)
        self.assertEqual(block.string.attributes, ['string_length', 'string_value'])
    def test_08_opcua_create_dependency_block(self):
        """Test dependecy block creation"""
        item_template_block = {"name": "body", "type": "depends:message_type"}
        block = opcua.OpcuaBlock(
                item_template_block={"name": "body", "type": "depends:message_type"},
                defaults={"message_type": "HEL"})
        self.assertEqual(block.name, "HEL_BODY")
    def test_09_opcua_create_dependency_block_missing(self):
        """Test nested block creation with missing defaults values"""
        with self.assertRaises(BOFProgrammingError):
            item_template_block = {"name": "body", "type": "depends:message_type"}
            block = opcua.OpcuaBlock(
                    item_template_block={"name": "body", "type": "depends:message_type"})
    def test_10_opcua_create_nested_dependecy_block_wrong(self):
        """Test nested block creation with wrong defaults values"""
        with self.assertRaises(BOFProgrammingError):
            item_template_block = {"name": "body", "type": "depends:message_type"}
            block = opcua.OpcuaBlock(
                item_template_block={"name": "body", "type": "depends:message_type"},
                defaults={"message_type": "unknown"})
    def test_11_opcua_create_block_with_value(self):
        """Test block creation with a value to fill it"""
        block = opcua.OpcuaBlock(type="STRING", value=14*b"\x01")
        self.assertEqual(block.string_length.value, b'\x01\x01\x01\x01')
    def test_12_opcua_create_block_with_value_missing_type(self):
        """Test that a block value with not type returns an empty list as expected"""
        block = opcua.OpcuaBlock()
        self.assertEqual(block.content, [])