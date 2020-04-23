"""unittest for ``bof.knx``.

- KNX empty frame instantiation
- Creating KNX Frames from identifiers from the specification
- Creating KNX Frames from byte arrays
- Access, modify, append data in KNX frames
"""

import unittest
from bof import knx, byte, BOFProgrammingError

class Test01BasicKnxFrame(unittest.TestCase):
    """Test class for basic KNX frame creation and usage."""
    def test_01_knxframe_init(self):
        """Test that a KnxFrame object is correctly created."""
        frame = knx.KnxFrame()
        self.assertTrue(isinstance(frame.header, knx.KnxStructure))
        self.assertTrue(isinstance(frame.body, knx.KnxStructure))
    def test_02_knxframe_header_init(self):
        """Test that frame header has been initialized with default values."""
        frame = knx.KnxFrame()
        self.assertEqual(bytes(frame.header), b"\x06\x10\x00\x00\x00\x06")
    def test_03_knxframe_header_field(self):
        """Test that frame header has been initialized with properties."""
        frame = knx.KnxFrame()
        self.assertEqual(bytes(frame.header.header_length), b"\x06")
        self.assertEqual(bytes(frame.header.protocol_version), b"\x10")
        self.assertEqual(bytes(frame.header.service_identifier), b"\x00\x00")
        self.assertEqual(bytes(frame.header.total_length), b"\x00\x06")
    def test_04_knxframe_header_from_sid(self):
        """Test that frame header has been initialized with properties."""
        frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
        self.assertEqual(bytes(frame.header.header_length), b"\x06")
        self.assertEqual(bytes(frame.header.protocol_version), b"\x10")
        self.assertEqual(bytes(frame.header.service_identifier), b"\x02\x03")
        self.assertEqual(bytes(frame.header.total_length), b"\x00\x0e")
    def test_05_knxframe_body_from_sid(self):
        """Test that frame body is initialized according to a valid sid."""
        frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
        self.assertEqual(bytes(frame.body.structure_length), b"\x08")
        self.assertEqual(bytes(frame.body.host_protocol_code), b"\x01")
        self.assertEqual(bytes(frame.body), b"\x08\x01\x00\x00\x00\x00\x00\x00")
    def test_06_knxframe_body_from_sid_update(self):
        """Test that a frame bu_ild from sid can be modified."""
        frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
        frame.body.ip_address.value = "192.168.1.33"
        self.assertEqual(bytes(frame.body.ip_address), b"\xc0\xa8\x01\x21")
        frame.body.port.value = 12
        self.assertEqual(bytes(frame.body.port), b"\x00\x0c")
        self.assertEqual(bytes(frame.body), b"\x08\x01\xc0\xa8\x01\x21\x00\x0c")
    def test_07_knxframe_body_from_sid_update_realvalues(self):
        """Test that a frame can be built from sid using real network link
        values from KNX connection.
        """
        knxnet = knx.KnxNet()
        knxnet.connect("localhost", 13671)
        frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
        ip, _ = knxnet.source # Returns 127.0.0.1, looks weird
        frame.body.ip_address.value = ip
        self.assertEqual(bytes(frame.body), b"\x08\x01\x7f\x00\x00\x01\x00\x00")

class Test02AdvancedKnxHeaderCrafting(unittest.TestCase):
    """Test class for advanced header fields handling and altering."""
    def test_01_basic_knx_header_from_frame(self):
        """Test basic header build from frame with toal_length update."""
        header = knx.KnxFrame().header
        self.assertEqual(bytes(header), b"\x06\x10\x00\x00\x00\x06")
    def test_02_basic_knx_header(self):
        """Test direct creation of a knx header, automated lengths update
        is disabled for total length (which is handled at frame level.
        """
        header = knx.KnxStructure(type="header")
        self.assertEqual(bytes(header), b"\x06\x10\x00\x00\x00\x00")
    def test_03_knx_header_resize(self):
        """Test that header length is resized automatically when modifying
        the size of a field.
        """
        header = knx.KnxStructure(type="header")
        header.service_identifier.size = 3
        header.update()
        self.assertEqual(byte.to_int(header.header_length.value), 7)
        self.assertEqual(bytes(header), b"\x07\x10\x00\x00\x00\x00\x00")
    def test_04_knx_header_resize_total_length(self):
        """Test that header length is updated when a field is expanded."""
        header = knx.KnxStructure(type="header")
        header.total_length.size = 3
        header.total_length.value = 123456
        header.update()
        self.assertEqual(bytes(header.header_length), b'\x07')
    def test_05_knx_header_resize(self):
        """Test that resize changes the value of the field's bytearray"""
        header = knx.KnxStructure(type="header")
        header.header_length.size = 2
        self.assertEqual(bytes(header.header_length), b'\x00\x06')
        header.update()
        self.assertEqual(bytes(header.header_length), b'\x00\x07')
    def test_06_knx_header_fixed_value(self):
        """Test that manual field value changes enable fixed_value boolean,
        which prevent from automatically updating the field.
        """
        header = knx.KnxStructure(type="header")
        header.header_length.value = b'\x02'
        self.assertEqual(bytes(header.header_length), b'\x02')
        header.update()
        self.assertEqual(bytes(header.header_length), b'\x02')
    def test_07_knx_header_set_content_different_size(self):
        """Test behavior when trying to set different size bytearrays 
        as field values."""
        header = knx.KnxStructure(type="header")
        header.service_identifier.value = b'\x10\x10\x10'
        self.assertEqual(bytes(header.service_identifier), b'\x10\x10')
        header.service_identifier.value = b'\x10'
        self.assertEqual(bytes(header.service_identifier), b'\x00\x10')
    def test_08_knx_header_set_invalid_content(self):
        """Test negative value for size."""
        header = knx.KnxStructure(type="header")
        header.header_length.size = -4
        self.assertEqual(header.header_length.size, -4)
        self.assertEqual(bytes(header.header_length), b'')
    def test_09_knx_header_set_invalid_content(self):
        """Test total length field behavior."""
        frame = knx.KnxFrame()
        frame.header.header_length.size = 2
        self.assertEqual(bytes(frame.header.total_length), b'\x00\x07')

class Test03AdvancedFieldCrafting(unittest.TestCase):
    """Test class for advanced structures and fields crafting."""
    def test_01_knx_create_field(self):
        """Test that we can craft a structure and assign it as frame header."""
        new_header = knx.KnxStructure()
        new_header.append(knx.KnxField(name="gasoline", size=3, value=666))
        self.assertIn("gasoline", new_header.attributes)
        self.assertEqual(bytes(new_header), b'\x00\x02\x9a')
    def test_02_knx_create_field_length(self):
        """Test that we can craft a structure and assign it as frame header."""
        new_header = knx.KnxStructure()
        new_header.append(knx.KnxField(name="gasoline", size=3, is_length=True))
        new_header.append(knx.KnxField(name="fuel", size=2, value=666))
        new_header.update()
        self.assertEqual(bytes(new_header.gasoline), b'\x00\x00\x05')
    def test_03_knx_remove_field_by_name(self):
        """Test that a field can be removed according to its name."""
        frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
        self.assertIn("ip_address", frame.body.attributes)
        frame.body.remove("ip_address")
        self.assertNotIn("ip_address", frame.body.attributes)
        self.assertEqual(bytes(frame.body), b'\x04\x01\x00\x00')
    def test_04_knx_multiple_fields_same_name(self):
        """Test the behavior in case multiple fields have the same name."""
        body = knx.KnxStructure()
        body.append(knx.KnxField(name="gasoline", size=1, value=1))
        body.append(knx.KnxField(name="gasoline", size=2, value=666))
        body.gasoline.value = 21
        self.assertEqual(bytes(body), b'\x01\x00\x15')
        body.remove("gasoline")
        self.assertEqual(bytes(body), b'\x00\x15')
    def test_05_knx_structception(self):
        """Test that we can do structception"""
        structure = knx.KnxStructure(name="atoll")
        structure.append(knx.KnxField(name="pom-"))
        structure.append(knx.KnxField(name="pom"))
        structure.append(knx.KnxStructure(name="galli"))
        structure.galli.append(knx.KnxField(name="sout pacific", value=b"10"))
        self.assertEqual(structure.attributes, ["pom_", "pom", "galli"])
        self.assertEqual([x.name for x in structure.fields], ["pom-", "pom", "sout pacific"])

class Test04DIBSpecificationClass(unittest.TestCase):
    """Test class for specification class building from JSON file."""
    def test_01_knx_spec_instantiate(self):
        spec = knx.KnxSpec()
        self.assertEqual(list(spec.service_identifiers.keys())[0], "SEARCH REQUEST")
    def test_01_knx_spec_clear(self):
        spec = knx.KnxSpec()
        spec.clear()
        with self.assertRaises(AttributeError):
            print(spec.service_identifiers)

class Test05DIBStructureFromSpec(unittest.TestCase):
    """Test class for structures with dib types (from a service identifier)."""
    def test_01_knx_structure_unknown_type(self):
        """Test that an exception is rose when creating a structure from
        an unknown template."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KnxStructure(type="WTF")
    def test_02_knx_structure_device_info(self):
        """Test that an exception is rose when creating a structure from
        an unknown template."""
        structure = knx.KnxStructure(type="DIB_DEVICE_INFO")
        self.assertEqual((byte.to_int(bytes(structure.structure_length))), 54)
    def test_03_knx_structure_supp_svc_families(self):
        """Test that special structure supported service families containing
        inner structure with repeat keyword is correctly instantiated.
        """
        structure = knx.KnxStructure(type="DIB_SUPP_SVC_FAMILIES")
        self.assertEqual(byte.to_int(structure.structure_length.value), 4)
        self.assertEqual(bytes(structure.service_family.id), b'\x00')
        self.assertEqual(bytes(structure.service_family.version), b'\x00')
        structure.append(knx.KnxStructure(type="SERVICE_FAMILY"))
        self.assertEqual(byte.to_int(structure.structure_length.value), 6)
    def test_04_knx_body_description_response(self):
        """Test correct building of a DESCRIPTION RESPONSE KNX frame."""
        frame = knx.KnxFrame(sid="DESCRIPTION_RESPONSE")
        self.assertEqual(bytes(frame.header.service_identifier), b'\x02\x04')
        frame.body.device_hardware.friendly_name.value = "sushi"
        frame.body.friendly_name.value = "pizza"
        self.assertEqual(bytes(frame.body.device_hardware.friendly_name).decode('utf-8'), "pizza")
    def test_05_knx_body_with_optional(self):
        """Test that we can build a frame with the optional keyword."""
        frame = knx.KnxFrame(sid="CONNECT REQUEST", optional=True)
        self.assertEqual(bytes(frame.body.port_2), b'\x00\x00')

class Test05ReceivedFrameParsing(unittest.TestCase):
    """Test class for received frame parsing."""
    def setUp(self):
        self.connection = knx.KnxNet()
        self.connection.connect("localhost", 13671)
    def tearDown(self):
        self.connection.disconnect()
    def test_01_knx_parse_descrresp(self):
        self.connection.send(knx.KnxFrame(sid="DESCRIPTION_REQUEST"))
        datagram = self.connection.receive()
        self.assertEqual(bytes(datagram.header.service_identifier), b"\x02\x04")
    def test_02_knx_parse_connectresp(self):
        connectreq = knx.KnxFrame(sid="CONNECT_REQUEST")
        self.connection.send(connectreq)
        connectresp = self.connection.receive()
        self.assertEqual(bytes(connectresp.header.service_identifier), b"\x02\x06")
        self.assertEqual(bytes(connectresp.body.status), b"\x00")
        self.assertEqual(bytes(connectresp.body.connection_response_data_block), b"\x02\x03")

class Test06CEMIFrameCrafting(unittest.TestCase):
    """Test class for KNX messages involving a cEMI frame."""
    def test_01_knx_config_req(self):
        """Test that cEMI frames definition in JSON is handled."""
        frame = knx.KnxFrame(sid="CONFIGURATION REQUEST", cemi="PropRead.req")
        self.assertEqual(bytes(frame.body.cemi.message_code), b"\xfc")
    def test_02_knx_single_cemi(self):
        """Test that we can build a single Structure from cEMI."""
        propwrite = knx.KnxStructure(cemi="PropWrite.con")
        self.assertEqual(bytes(propwrite.message_code), b"\xf5")
