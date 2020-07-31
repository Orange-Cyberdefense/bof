"""unittest for ``bof.opcua``.

- OPC UA specification gathering
"""

import unittest
from bof import opcua, BOFLibraryError

class Test01OpcuaSpec(unittest.TestCase):
    """Test class for specification class building from JSON file."""
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
