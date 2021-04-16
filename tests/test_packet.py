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
        # we check that it correctly initializes its attributes
        self.assertEqual(bof_pkt.type, "BOFPacket")
        self.assertEqual(bof_pkt.scapy_pkt.__class__, Packet().__class__)

    def test_0102_bofpacket_child_construct(self):
        """Test that we can build an object inheriting from BOFPacket."""
        from tests.test_layers.otter.otter_packet import BOFBasicOtterPacket1
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1
        bof_pkt = BOFBasicOtterPacket1()
        # we check that it correctly initializes its attributes
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

    def test_0303_bofpacket_iter(self):
        """Test that str() prints Scapy packet fields."""
        self.assertEqual([x.name for x in self.bof_pkt], [x.name for x in self.scapy_pkt.fields_desc])


class Test04PayloadAddition(unittest.TestCase):
    """Test class for raw BOFPacket initialization.
    Note that BOFPacket are not supposed to be instantiated directly.
    """

    def test_0401_bofpacket_addpayload_base_scapy(self):
        """Test that we can add a Scapy layer as a payload for a BOFPacket's scapy_pkt."""
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1, ScapyBasicOtterPacket2
        # We want ScapyBasicOtterPacket2 as payload for Scapy ScapyBasicOtterPacket1, which are already bound
        bof_pkt = BOFPacket()
        bof_pkt.scapy_pkt = ScapyBasicOtterPacket1()
        bof_pkt.add_payload(ScapyBasicOtterPacket2())
        self.assertEqual(bof_pkt.scapy_pkt.payload.get_field("basic_otter_2_1").name, "basic_otter_2_1")
        self.assertEqual(bof_pkt.scapy_pkt.getlayer("ScapyBasicOtterPacket2").get_field("basic_otter_2_1").name, "basic_otter_2_1")
        self.assertEqual(bytes(bof_pkt), bytes(ScapyBasicOtterPacket1())+bytes(ScapyBasicOtterPacket2()))

    def test_0402_bofpacket_addpayload_base_bof(self):
        """Test that we can add a BOFPacket as payload for another BOFPacket."""
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1, ScapyBasicOtterPacket2
        # We want ScapyBasicOtterPacket1 as payload for Scapy UDP, which are already bound
        # in our Scapy protocol implementation
        bof_pkt1 = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())
        bof_pkt2 = BOFPacket(scapy_pkt=ScapyBasicOtterPacket2())
        bof_pkt1.add_payload(bof_pkt2)
        self.assertEqual(bof_pkt1.scapy_pkt.payload.get_field("basic_otter_2_1").name, "basic_otter_2_1")
        self.assertEqual(bof_pkt1.scapy_pkt.getlayer("ScapyBasicOtterPacket2").get_field("basic_otter_2_1").name,
                         "basic_otter_2_1")
        self.assertEqual(bytes(bof_pkt1), bytes(ScapyBasicOtterPacket1()) + bytes(ScapyBasicOtterPacket2()))

    def test_0403_bofpacket_addpayload_automatic(self):
        """Test that we can dynamically bind payloads."""
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1, ScapyBasicOtterPacket3
        from scapy.compat import raw
        # We want ScapyBasicOtterPacket3 as payload for ScapyBasicOtterPacket1, while they are not bound in
        # our Scapy protocol implementation
        bof_pkt = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())
        bof_pkt.add_payload(ScapyBasicOtterPacket3(), autobind=True)
        self.assertEqual(bof_pkt.scapy_pkt.payload.get_field("basic_otter_3_1").name, "basic_otter_3_1")
        self.assertEqual(bof_pkt.scapy_pkt.getlayer("ScapyBasicOtterPacket3").get_field("basic_otter_3_1").name, "basic_otter_3_1")
        self.assertEqual(bytes(bof_pkt), bytes(ScapyBasicOtterPacket1()) + bytes(ScapyBasicOtterPacket3()))
        # effectively tests for "logical" payload binding (in addition to the correct frame bytes)
        self.assertEqual(bof_pkt.scapy_pkt.__class__(raw(bof_pkt.scapy_pkt)).payload.name, "basic_otter_packet_3")

    def test_0404_bofpacket_addpayload_automatic_layer(self):
        """Test that we can dynamically bind payloads even
        even if the target is not the first layer.
        (This was a bug because we were not binding with the last) """
        from tests.test_layers.raw_scapy.otter import ScapyBasicOtterPacket1, ScapyBasicOtterPacket2, ScapyBasicOtterPacket3
        from scapy.compat import raw
        # We start with ScapyBasicOtterPacket2 as payload for ScapyBasicOtterPacket1, expected because bound in
        # our Scapy protocol implementation
        # We then add ScapyBasicOtterPacket3 as payload for ScapyBasicOtterPacket2, not bound by default
        bof_pkt1 = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1()/ScapyBasicOtterPacket2())
        bof_pkt1.add_payload(ScapyBasicOtterPacket3(), autobind=True)
        self.assertEqual(bof_pkt1.scapy_pkt.payload.payload.get_field("basic_otter_3_1").name, "basic_otter_3_1")
        self.assertEqual(bof_pkt1.scapy_pkt.getlayer("ScapyBasicOtterPacket3").get_field("basic_otter_3_1").name,
                         "basic_otter_3_1")
        self.assertEqual(bytes(bof_pkt1), bytes(ScapyBasicOtterPacket1()) + bytes(ScapyBasicOtterPacket2()) + bytes(ScapyBasicOtterPacket3()))
        # effectively tests for "logical" payload binding (in addition to the correct frame bytes)
        self.assertEqual(bof_pkt1.scapy_pkt.__class__(raw(bof_pkt1.scapy_pkt)).payload.payload.name, "basic_otter_packet_3")
        pass

    def test_0405_bofpacket_addpayload_automatic_guess(self): # TODO
        """Test dynamic payload binding when specific conditions are used
         via guess_payload in Scapy implementation"""
        pass
