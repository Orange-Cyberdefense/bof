"""unittest for ``bof.knx``.

- KNX empty frame instantiation
- Creating KNX Frames from identifiers from the specification
- Creating KNX Frames from byte arrays
- Access, modify, append data in KNX frames
"""

import unittest
from bof import knx, byte

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
        knxnet.connect("localhost", 13671, init=False)
        frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
        ip, port = knxnet.source # Returns 127.0.0.1, looks weird
        frame.body.ip_address.value = ip
        self.assertEqual(bytes(frame.body), b"\x08\x01\x7f\x00\x00\x01\x00\x00")
