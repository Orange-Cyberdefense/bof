"""unittest for opcua frame, implementing ``bof.frame``'s
``BOFSpec``, ``BOFFrame``, ``BOFBlock`` and ``BOFField`` classes.
"""

import unittest
from bof import opcua, byte, BOFLibraryError, BOFProgrammingError
from pathlib import PurePosixPath

class Test01OpcuaSpec(unittest.TestCase):
    """Test class for OpcuaSpec.
    Note that we don't test for the whole BOFSpec behavior, but
    uniquely what we are using in OpcuaSpec. Therefore more test
    might be needed as OPC UA protocol implementation progresses.
    """
    def test_01_opcua_spec_instantiate_default(self):
        """Test that the current default `opcua.json` file is valid."""
        try:
            spec = opcua.OpcuaSpec()
        except BOFLibraryError:
            self.fail("Default opcua.json should not raise BOFLibraryError.")
    def test_02_opcua_spec_instantiate_custom_valid(self):
        """Test that a valid specified OPC UA spec file works as expected."""
        try:
            spec = opcua.OpcuaSpec()
            spec.clear()
            spec.load("tests/jsons/valid.json")
        except BOFLibraryError:
            self.fail("Valid json spec should not raise BOFLibraryError.")
    def test_03_opcua_spec_instantiate_custom_invalid_json(self):
        """Test that an invalid specified OPC UA json raises exception."""
        with self.assertRaises(BOFLibraryError):
            spec = opcua.OpcuaSpec()
            spec.clear()
            spec.load("tests/jsons/invalid.json")
    def test_04_opcua_spec_instantiate_custom_invalid_path(self):
        """Test an invalid spec file path raises exception."""
        with self.assertRaises(BOFLibraryError):
            spec = opcua.OpcuaSpec()
            spec.clear()
            spec.load("tests/jsons/unexisting.json")
    def test_05_opcua_spec_property_access_valid(self):
        """Test that a JSON element can be accessed as property"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        frame_template = spec.frame
        self.assertEqual(frame_template[0]["name"], "header")
    def test_06_opcua_spec_property_access_invalid(self):
        """Test that a unexisting JSON element can't be accessed as property"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        with self.assertRaises(AttributeError):
            frame_template = spec.unexisting
    def test_07_opcua_spec_get_block_template_valid(self):
        """Test that we can get block template from spec as expected"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        block_template = spec.get_block_template(block_name="HEADER")
        expected_template = [{'name': 'message_type', 'type': 'field', 'size': 3},
                             {'name': 'is_final', 'type': 'field', 'size': 1}, 
                             {'name': 'message_size', 'type': 'field', 'size': 4}]
        self.assertEqual(block_template, expected_template)
    def test_08_opcua_spec_get_block_template_invalid(self):
        """Test that an invalid block request returns None"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        block_template = spec.get_block_template(block_name="INVALID")
        self.assertEqual(block_template, None)
    def test_09_opcua_spec_get_item_template_valid(self):
        """Test that we can get an item from spec as expected"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        item_template = spec.get_item_template("HEADER", "message_size")
        expected_template = {'name': 'message_size', 'type': 'field', 'size': 4}
        self.assertEqual(item_template, expected_template)
    def test_10_opcua_spec_get_item_invalid(self):
        """Test that an invalid item request returns None"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        item_template = spec.get_item_template("INVALID", "INVALID")
        self.assertEqual(item_template, None)
    def test_11_get_code_value_str_valid(self):
        """Test that a valid code value can be retrieved from str key"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        message_structure = spec.get_code_value("message_type", "HEL")
        self.assertEqual(message_structure, "HEL_BODY")
    def test_12_get_code_value_str_invalid(self):
        """Test that an invalid code value returns None"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        message_structure = spec.get_code_value("INVALID", "INVALID")
        self.assertEqual(message_structure, None)
    def test_13_get_code_value_bytes_valid(self):
        """Test that valid code value can be retrieved from bytes key"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        message_structure = spec.get_code_value("message_type", b"HEL")
        self.assertEqual(message_structure, "HEL_BODY")
    def test_14_get_code_value_bytes_hex_identifier(self):
        """Test that an hex code value can be retrieved from bytes key"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        code_value = spec.get_code_value("node_id_value", b'\xbe\x01')
        self.assertEqual(code_value, "OPEN_SECURE_CHANNEL_REQUEST")
    def test_15_get_code_value_bytes_invalid(self):
        """Test that None is returned when code value is searched with invalid key"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        message_structure = spec.get_code_value("INVALID", b"INVALID")
        self.assertEqual(message_structure, None)

class Test02OpcuaField(unittest.TestCase):
    """Test class for field crafting and access.
    Note that we don't test for the whole BOFField behavior, but
    uniquely what we are using in OpcuaField. Therefore more test
    might be needed as OPC UA protocol implementation progresses.
    """
    def test_01_opcua_field_create_manual(self):
        """Test that we can craft a field by hand and content is set"""
        field = opcua.OpcuaField(name="message_type", size=3, value=byte.from_int(1, 3, 'little'))
        self.assertEqual(field.name, "message_type")
        self.assertEqual(field.size, 3)
        self.assertEqual(field.value, b"\x01\x00\x00")
    def test_02_opcua_field_create_template(self):
        """Test that we can craft a field from a template and content is set"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load("tests/jsons/valid.json")
        item_template_field = spec.get_item_template("HEADER", "message_type")
        field = opcua.OpcuaField(**item_template_field)
        self.assertEqual(field.name, "message_type")
        self.assertEqual(field.size, 3)
    def test_03_opcua_field_set(self):
        """Test that a field value can get set as expected."""
        field = opcua.OpcuaField(name="message_type", size=3)
        field.value = b'\x01\x00\x00'
        self.assertEqual(field.value, b'\x01\x00\x00')
    def test_04_opcua_field_orphan_path(self):
        """Test that a field path is correctly set to self if no parent is specified"""
        field = opcua.OpcuaField(name="message_type", size=3)
        self.assertEqual(field._path, PurePosixPath('message_type'))

class Test03OpcuaBlockBase(unittest.TestCase):
    """Test class for block crafting and access.
    Note that we don't test for the whole BOFBlock behavior, but
    uniquely what we are using in OpcuaBlock. Therefore more test
    might be needed as OPC UA protocol implementation progresses.
    """
    def test_01_opcua_block_create_empty(self):
        """Test that an empty block can be created and returns an empty list of fields"""
        block = opcua.OpcuaBlock()
        self.assertEqual(block.content, [])
    def test_02_opcua_block_create_template_valid(self):
        """Test that a block can be created as expected from a template"""
        item_template_block = {"name": "header", "type": "HEADER"}
        block = opcua.OpcuaBlock(**item_template_block)
        expected_attributes = ['message_type', 'is_final', 'message_size']
        self.assertEqual(block.attributes, expected_attributes)
    def test_03_opcua_block_create_template_invalid(self):
        """Tests that block creation with invalid template fail case is handled"""
        with self.assertRaises(BOFProgrammingError):
            item_template_block = {"name": "header", "type": "unknown"}
            block = opcua.OpcuaBlock(**item_template_block)
    def test_04_opcua_block_create_type_valid(self):
        """Tests that a block can be created as expected from a type name"""
        block = opcua.OpcuaBlock(type="HEADER")
        expected_attributes = ['message_type', 'is_final', 'message_size']
        self.assertEqual(block.attributes, expected_attributes)
    def test_05_opcua_block_create_type_invalid(self):
        """Tests that block creation with invalid type name fail case is handled"""
        with self.assertRaises(BOFProgrammingError):
            block = opcua.OpcuaBlock(type="unknown")
    def test_06_opcua_block_create_nested_block(self):
        """Test for manual creation of nested block"""
        block = opcua.OpcuaBlock(name="empty_block", type="EMPTY")
        sub_block = opcua.OpcuaBlock(name="sub_block", type="HEADER", parent=block)
        block.append(sub_block)
        expected_attributes = ['message_type', 'is_final', 'message_size']
        self.assertEqual(block.sub_block.attributes, expected_attributes)
    def test_07_opcua_block_create_value(self):
        """Test block creation with a value to fill it"""
        header_bytes = bytes.fromhex('48454c4638000000')
        block = opcua.OpcuaBlock(type="HEADER", value=header_bytes)
        self.assertEqual(block.message_type.value, b'HEL')
    def test_08_opcua_block_orphan_path(self):
        """Test that a block path is correctly set to self if no parent is specified"""
        block = opcua.OpcuaBlock(type="HEADER")
        self.assertEqual(block._path, PurePosixPath('header'))
    def test_09_opcua_block_sub_block_path(self):
        """TODO: add when use-case comes up"""
    def test_10_opcua_block_sub_field_path(self):
        """Test that a sub-block field is correctly set using its parent path"""
        block = opcua.OpcuaBlock(type="HEADER")
        self.assertEqual(block.message_size._path, PurePosixPath('header/message_size'))

class Test04OpcuaBlockDepends(unittest.TestCase):
    """Test class for dependency-related block behavior.
    Note that we don't test for the whole BOFBlock behavior, but
    uniquely what we are using in OpcuaBlock. Therefore more test
    might be needed as OPC UA protocol implementation progresses.
    """
    def test_01_opcua_block_dependency_base_valid(self):
        """Test base dependency search mechanism within blocks"""
        block = opcua.OpcuaBlock(name="fake_frame")
        block.append(opcua.OpcuaBlock(**{"name": "header", "type": "HEADER"}, parent=block))
        block.header.message_type.value = b'HEL'
        block.append(opcua.OpcuaBlock(**{"name": "body", "type": "depends:message_type"}, parent=block))
        expected_attributes = ['protocol_version', 'receive_buffer_size', 'send_buffer_size', 
                               'max_message_size', 'max_chunk_count', 'endpoint_url_length',
                               'endpoint_url']
        self.assertEqual(block.body.attributes, expected_attributes)
    def test_02_opcua_block_dependency_base_invalid(self):
        """Test that missing dependency causes an error"""
        with self.assertRaises(BOFProgrammingError):
            item_template_block = {"name": "body", "type": "depends:message_type"}
            block = opcua.OpcuaBlock(**{"name": "body", "type": "depends:message_type"})
    def test_03_opcua_block_dependency_user_value_valid(self):
        """Test dependency search with user supplied value"""
        block = opcua.OpcuaBlock(**{"name": "body", "type": "depends:message_type"},
                                 user_values={'message_type':'HEL'})
        expected_attributes = ['protocol_version', 'receive_buffer_size', 'send_buffer_size', 
                               'max_message_size', 'max_chunk_count', 'endpoint_url_length',
                               'endpoint_url']
        self.assertEqual(block.attributes, expected_attributes)
    def test_04_opcua_block_dependency_user_value_invalid(self):
        """Test dependency search with invalid user supplied value"""
        with self.assertRaises(BOFProgrammingError):
            block = opcua.OpcuaBlock(**{"name": "body", "type": "depends:message_type"},
                                    user_values={'message_type':'INVALID'})
    def test_05_opcua_block_dependency_bytes_valid(self):
        """Test dependency search within blocks created from raw bytes"""
        data1 = b'HEL\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data2 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        block = opcua.OpcuaBlock(name="fake_frame")
        block.append(opcua.OpcuaBlock(value=data1, parent=block, **{"name": "header", "type": "HEADER"}))
        block.append(opcua.OpcuaBlock(value=data2, parent=block, **{"name": "body", "type": "depends:message_type"}))
        expected_attributes = ['protocol_version', 'receive_buffer_size', 'send_buffer_size', 
                               'max_message_size', 'max_chunk_count', 'endpoint_url_length',
                               'endpoint_url']
        self.assertEqual(block.body.attributes, expected_attributes)
    def test_06_opcua_block_dependency_bytes_invalid(self):
        """Test that invalid byte dependency causes an error"""
        data1 = b'NAN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data2 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        block = opcua.OpcuaBlock(name="fake_frame")
        block.append(opcua.OpcuaBlock(value=data1, parent=block, **{"name": "header", "type": "HEADER"}))
        with self.assertRaises(BOFProgrammingError):
            block.append(opcua.OpcuaBlock(value=data2, parent=block, **{"name": "body", "type": "depends:message_type"}))
    def test_07_opcua_block_dependency_bitfield(self):
        """Test that bit-field dependency works as expected"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load('tests/jsons/mask.json')
        user_values={"has_opt_1, has_opt_2, has_opt_3, has_opt_4, has_opt_5, has_opt_6, has_opt_7, has_opt_8": b'\x94'}
        block = opcua.OpcuaBlock(spec=spec, type='BLOCK', user_values=user_values)
        sub_fields = []
        for field in block:
            if isinstance(field.name, str) and field.name.startswith('optional') and field.name.endswith('field'):
                sub_fields.append(field.name)
        expected_fields = ['optional_3_field', 'optional_5_field', 'optional_8_field']
        self.assertEqual(sub_fields, expected_fields)
    def test_08_opcua_block_dependency_key(self):
        """Test that a dependency can be found in any field attribute (not only value)"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load('tests/jsons/dependencies.json')
        block = opcua.OpcuaBlock(spec=spec, type='TEST_BLOCK')
        self.assertEqual(block.test_field_2.value, b'\x01')
    def test_09_opcua_block_dependency_key_default(self):
        """Test that if not specified, dependency will look into the value"""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load('tests/jsons/dependencies.json')
        block = opcua.OpcuaBlock(spec=spec, type='TEST_BLOCK')
        self.assertEqual(block.test_field_3.value, b'\x02')
    def test_10_opcua_block_dependency_key_invalid(self):
        """Test that a missing attribute will result in an error"""
        with self.assertRaises(BOFProgrammingError):
            spec = opcua.OpcuaSpec()
            spec.clear()
            spec.load('tests/jsons/dependencies.json')
            block = opcua.OpcuaBlock(spec=spec, type='TEST_BLOCK_INVALID')
    def test_11_opcua_block_dependency_parent(self):
        """Test that we can retrieve a specific field even if present multiple
        times by specifying a parent level to look at.
        """
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load('tests/jsons/dependencies.json')
        block = opcua.OpcuaBlock(spec=spec, type='PARENT_2')
        self.assertEqual(block.parent_1.parent_0.test_field_grandparent.value, b'\x02')
        self.assertEqual(block.parent_1.parent_0.test_field_parent.value, b'\x01')
    def test_12_opcua_block_dependency_parent_default(self):
        """Test that if no parent level specified, will look for the closest one."""
        spec = opcua.OpcuaSpec()
        spec.clear()
        spec.load('tests/jsons/dependencies.json')
        block = opcua.OpcuaBlock(spec=spec, type='PARENT_2')
        self.assertEqual(block.parent_1.parent_0.test_field_parent_default.value, b'\x01')
    def test_13_opcua_block_dependency_parent_invalid(self):
        """Test that specifying a too high level will result in an error"""
        with self.assertRaises(BOFProgrammingError):
            spec = opcua.OpcuaSpec()
            spec.clear()
            spec.load('tests/jsons/dependencies.json')
            # block PARENT_0 should not (and cannot) be instanciated directly
            # it needs parents to look for dependency in
            block = opcua.OpcuaBlock(spec=spec, type='PARENT_0')

class Test05OpcuaFrameBase(unittest.TestCase):
    def test_01_opcua_frame_create_empty(self):
        """Test that because OPC UA has a dependency directly in its frame that
        defines its whole structure, an empty frame cannot be created on itself.
        """
        with self.assertRaises(BOFProgrammingError):
            frame = opcua.OpcuaFrame()
        return
    def test_02_opcua_frame_create_user_args_UACP(self):
        """Test that an OPC UA simple frame from UACP can be created from user
        supplied parameter. Here with frame type HEL.
        """
        frame = opcua.OpcuaFrame(type='HEL')
        expected_attributes = ['message_type', 'is_final', 'message_size',
                               'protocol_version', 'receive_buffer_size', 
                               'send_buffer_size', 'max_message_size', 
                               'max_chunk_count', 'endpoint_url_length', 
                               'endpoint_url']
        self.assertEqual(frame.attributes, expected_attributes)
    def test_03_opcua_frame_create_bytes_UACP(self):
        """Test that an OPC UA simple frame from UACP can be created from raw
        bytes values. Here with frame type HEL.
        """
        hel_data = bytes.fromhex('48454c463800000000000000ffff0000ffff00000000000000000000180000006f70632e7463703a2f2f6c6f63616c686f73743a34383430')
        frame = opcua.OpcuaFrame(bytes=hel_data)
        expected_attributes = ['message_type', 'is_final', 'message_size',
                               'protocol_version', 'receive_buffer_size', 
                               'send_buffer_size', 'max_message_size', 
                               'max_chunk_count', 'endpoint_url_length', 
                               'endpoint_url']
        self.assertEqual(frame.attributes, expected_attributes)
        return
