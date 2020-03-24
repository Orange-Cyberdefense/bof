"""unittest for ``bof.knx``.

- KNX empty frame instantiation
- Creating KNX Frames from identifiers from the specification
- Creating KNX Frames from byte arrays
- Access, modify, append data in KNX frames
"""

import unittest
from bof import knx

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
        self.assertEqual(bytes(frame.header), b"\x06\x10\x00\x00\x00\x00")
