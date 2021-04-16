"""unittest for ``bof.packet``

- BOFPacket and BOFPacket child class initialization
- Link between BOFPacket classes and Scapy objects below
- BOFPacket-inherited objects handling and usage
- BOFPacket layers and fields manipulations
"""

import unittest
from scapy.contrib.modbus import ModbusADURequest
from bof.packet import *


class Test01PacketConstruct(unittest.TestCase):
    """Test class for raw BOFPacket initialization.
    Note that BOFPacket are not supposed to be instantiated directly.
    """

    def test_0101_bofpacket_construct(self):
        """Test empty constructor."""
        bof_pkt = BOFPacket()
        self.assertEqual(bof_pkt.type, "BOFPacket")

    def test_0102_bofpacket_child_construct(self):
        """Test that we can build an object inheriting from BOFPacket."""
        from tests.test_layers.otter.otter_packet import BOFBasicOtterPacket1
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1
        bof_pkt = BOFBasicOtterPacket1()
        self.assertEqual(bof_pkt.name, "BOFBasicOtterPacket1")
        self.assertEqual(bof_pkt.scapy_pkt.__class__, ScapyBasicOtterPacket1().__class__)

    def test_0103_bofpacket_scapy_param_construct(self):
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1
        """Test scapy_pkt parameter in constructor"""
        bof_pkt = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())
        self.assertEqual(bof_pkt.scapy_pkt.__class__, ScapyBasicOtterPacket1().__class__)


class Test02ScapyLayersAccess(unittest.TestCase):
    """Test class to make sure that we access Scapy layer content."""

    def test_0201_bofpacket_scapylayer_integrated(self):
        """Test that we can build BOFPacket from layer in scapy library."""
        bof_pkt = BOFPacket(scapy_pkt=ModbusADURequest())
        self.assertEqual(bof_pkt.scapy_pkt.name, "ModbusADU")

    def test_0202_bofpacket_scapylayer_standalone(self):
        """Test that we can build BOFPacket from layer as standalone file.
        The standalone file shall have a protocol written with scapy format.
        """
        from bof.layers.raw_scapy.knx import KNX
        bof_pkt = BOFPacket(scapy_pkt=KNX())
        self.assertEqual(bof_pkt.scapy_pkt.name, "KNXnet/IP")


class Test03PacketBuiltins(unittest.TestCase):
    """Test class for raw BOFPacket builtin function overload."""

    @classmethod
    def setUpClass(self):
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1
        self.scapy_pkt = ScapyBasicOtterPacket1()
        self.bof_pkt = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())

    def test_0301_bofpacket_bytes(self):
        """Test that bytes() prints Scapy packet bytes."""
        self.assertEqual(bytes(self.bof_pkt), bytes(self.scapy_pkt))
        self.assertEqual(bytes(self.bof_pkt), b'\x01\x02')

    def test_0302_bofpacket_len(self):
        """Test that len() prints Scapy packet length."""
        self.assertEqual(len(self.bof_pkt), len(self.scapy_pkt))
        self.assertEqual(len(self.bof_pkt), 2)

    def test_0304_bofpacket_iter(self):
        """Test that str() prints Scapy packet fields."""
        self.assertEqual([x.name for x in self.bof_pkt], [x.name for x in self.scapy_pkt.fields_desc])

