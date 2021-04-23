"""unittest for ``bof.packet``

- BOFPacket and BOFPacket child class initialization
- Link between BOFPacket classes and Scapy objects below
- BOFPacket-inherited objects handling and usage
- BOFPacket layers and fields manipulations
"""

import unittest
# Scapy
from scapy.contrib.modbus import ModbusADURequest
from scapy.compat import raw
#Internal
from bof import BOFProgrammingError, BOFPacket
from tests.test_layers.otter.otter_packet import BOFBasicOtterPacket1
from tests.test_layers.raw_scapy.otter import *

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
        bof_pkt = BOFBasicOtterPacket1()
        self.assertEqual(bof_pkt.name, "BOFBasicOtterPacket1")
        self.assertEqual(bof_pkt.scapy_pkt.__class__, ScapyBasicOtterPacket1().__class__)
        raw(bof_pkt) # Should raise Exception if wrong

    def test_0103_bofpacket_scapy_param_construct(self):
        """Test scapy_pkt parameter in constructor"""
        bof_pkt = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())
        self.assertEqual(bof_pkt.scapy_pkt.__class__, ScapyBasicOtterPacket1().__class__)
        self.assertEqual(bof_pkt.basic_otter_1_2, 0x02)
        raw(bof_pkt) # Should raise Exception if wrong

    def test_0104_bofpacket_scapy_attr_init(self):
        """Test that we can set values to fields in constructor (same type)."""
        bof_pkt = BOFBasicOtterPacket1(basic_otter_1_2=0x03)
        self.assertEqual(bof_pkt.basic_otter_1_2, 0x03)
        raw(bof_pkt) # Should raise Exception if wrong

    def test_0105_bofpacket_scapy_attr_init_othertype(self):
        """Test that we can set values to fields in constructor (any type: str)."""
        bof_pkt = BOFBasicOtterPacket1(basic_otter_1_2="test")
        self.assertEqual(bof_pkt.basic_otter_1_2, "test")
        self.assertEqual(bof_pkt["basic_otter_1_2"], b"test")
        raw(bof_pkt) # Should raise Exception if wrong

    def test_0106_bofpacket_scapy_attr_init_othertype_bytes(self):
        """Test that we can set values to fields in constructor (any type: bytes)."""
        bof_pkt = BOFBasicOtterPacket1(basic_otter_1_2=b"\x42")
        self.assertEqual(bof_pkt.basic_otter_1_2, b"\x42")
        self.assertEqual(bof_pkt["basic_otter_1_2"], b"\x42")
        raw(bof_pkt) # Should raise Exception if wrong

    def test_0107_bofpacket_scapy_attr_init_invalid(self):
        """Test that settings values to unknown fields raises exceptions."""
        with self.assertRaises(BOFProgrammingError):
            bof_pkt = BOFBasicOtterPacket1(basic_otter_unknown=0x03)

class Test02ScapyLayersAccess(unittest.TestCase):
    """Test class to make sure that we access Scapy layer content."""

    def test_0201_bofpacket_scapylayer_integrated(self):
        """Test that we can build BOFPacket from layer in scapy library.
        BOFPacket should not be instantiated directly.
        """
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
        self.assertEqual([x.name for x in self.bof_pkt],
                         [x.name for x in self.scapy_pkt.fields_desc])

class Test04Fields(unittest.TestCase):
    """Test class for Scapy Fields' management from ``BOFPacket``."""
    @classmethod
    def setUp(self):
        self.bof_pkt = BOFBasicOtterPacket1()

    def test_0401_field_readvalue(self):
        """Test that we can get the value of a field directly."""
        self.assertEqual(self.bof_pkt.basic_otter_1_1, 0x01)
        self.assertEqual(self.bof_pkt.scapy_pkt.basic_otter_1_1, 0x01)

    def test_0402_field_readbytes(self):
        """Test that we can get the value of a field directly."""
        self.assertEqual(self.bof_pkt["basic_otter_1_1"], b"\x01")

    def test_0403_field_writevalue_sametype(self):
        """Test that we can change the value of a field directly."""
        self.bof_pkt.basic_otter_1_2 = 42
        self.assertEqual(self.bof_pkt.basic_otter_1_2, 42)
        raw(self.bof_pkt) # Should raise Exception if wrong

    def test_0404_field_writevalue_othertype_bytes(self):
        """Test that we can change the value of a field with different type."""
        self.bof_pkt.basic_otter_1_2 = b"\x42\x42"
        self.assertEqual(self.bof_pkt.basic_otter_1_2, b"\x42\x42")
        raw(self.bof_pkt) # Should raise Exception if wrong

    def test_0405_field_writevalue_othertype_special(self):
        """Test that we can change the value of a field with special type."""
        self.bof_pkt.basic_otter_1_2 = "192.168.1.2"
        self.assertEqual(self.bof_pkt.basic_otter_1_2, "192.168.1.2")
        self.assertEqual(self.bof_pkt["basic_otter_1_2"], b"\xc0\xa8\x01\x02")
        raw(self.bof_pkt) # Should raise Exception if wrong

class Test05PayloadAddition(unittest.TestCase):
    """Test for BOFPacket's payload addition functionality (append())"""

    def test_0501_bofpacket_addpayload_base_scapy(self):
        """Test that we can add a Scapy layer as a payload for a scapy_pkt.
        ScapyBasicOtterPacket2 should be a payload for ScapyBasicOtterPacket1.
        """
        bof_pkt = BOFPacket()
        bof_pkt.scapy_pkt = ScapyBasicOtterPacket1()
        bof_pkt.append(ScapyBasicOtterPacket2())
        self.assertEqual(bof_pkt.scapy_pkt.payload.get_field("basic_otter_2_1").name,
                         "basic_otter_2_1")
        self.assertEqual(bof_pkt.scapy_pkt.getlayer("ScapyBasicOtterPacket2").get_field("basic_otter_2_1").name,
                         "basic_otter_2_1")
        self.assertEqual(bytes(bof_pkt), bytes(ScapyBasicOtterPacket1())+bytes(ScapyBasicOtterPacket2()))

    def test_0502_bofpacket_addpayload_base_bof(self):
        """Test that we can add a BOFPacket as payload for another BOFPacket."""
        bof_pkt1 = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())
        bof_pkt2 = BOFPacket(scapy_pkt=ScapyBasicOtterPacket2())
        bof_pkt1.append(bof_pkt2)
        self.assertEqual(bof_pkt1.scapy_pkt.payload.get_field("basic_otter_2_1").name, "basic_otter_2_1")
        self.assertEqual(bof_pkt1.scapy_pkt.getlayer("ScapyBasicOtterPacket2").get_field("basic_otter_2_1").name,
                         "basic_otter_2_1")
        self.assertEqual(bytes(bof_pkt1), bytes(ScapyBasicOtterPacket1()) + bytes(ScapyBasicOtterPacket2()))

    def test_0503_bofpacket_addpayload_automatic(self):
        """Test that we can dynamically bind payloads.
        ScapyBasicOtterPacket 1 and 3 are not bound in Scapy implementation.
        """
        bof_pkt = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1())
        bof_pkt.append(ScapyBasicOtterPacket3(), autobind=True)
        self.assertEqual(bof_pkt.scapy_pkt.payload.get_field("basic_otter_3_1").name,
                         "basic_otter_3_1")
        self.assertEqual(bof_pkt.scapy_pkt.getlayer("ScapyBasicOtterPacket3").get_field("basic_otter_3_1").name,
                         "basic_otter_3_1")
        self.assertEqual(bytes(bof_pkt), bytes(ScapyBasicOtterPacket1())
                         + bytes(ScapyBasicOtterPacket3()))
        # effectively tests for "logical" payload binding (in addition to the correct frame bytes)
        self.assertEqual(bof_pkt.scapy_pkt.__class__(raw(bof_pkt.scapy_pkt)).payload.name, "basic_otter_packet_3")

    def test_0504_bofpacket_addpayload_automatic_layer(self):
        """Test that we can bind payloads with another layer than the 1st one.
        (This was a bug because we were not binding with the last)
        Here, Packet 2 is bound to 1, but Packet 2 is not bound to 3 by default.
        """
        bof_pkt1 = BOFPacket(scapy_pkt=ScapyBasicOtterPacket1()/ScapyBasicOtterPacket2())
        bof_pkt1.append(ScapyBasicOtterPacket3(), autobind=True)
        self.assertEqual(bof_pkt1.scapy_pkt.payload.payload.get_field("basic_otter_3_1").name,
                         "basic_otter_3_1")
        self.assertEqual(bof_pkt1.scapy_pkt.getlayer("ScapyBasicOtterPacket3").get_field("basic_otter_3_1").name,
                         "basic_otter_3_1")
        self.assertEqual(bytes(bof_pkt1), bytes(ScapyBasicOtterPacket1())
                         + bytes(ScapyBasicOtterPacket2())
                         + bytes(ScapyBasicOtterPacket3()))
        # effectively tests for "logical" payload binding (in addition to the correct frame bytes)
        self.assertEqual(bof_pkt1.scapy_pkt.__class__(raw(bof_pkt1.scapy_pkt)).payload.payload.name,
                         "basic_otter_packet_3")

    @unittest.skip("Not implemented yet.")
    def test_0505_bofpacket_addpayload_automatic_guess(self): # TODO
        """Test dynamic payload binding when specific conditions are used
         via guess_payload in Scapy implementation"""
        pass


class Test06PacketClassClone(unittest.TestCase):
    """Test for Scapy packet/layer duplication (clone_pkt_class())"""

    def test_0601_packet_clone_edit_classattr(self):
        """Test that packet cloning creates a separate instance of the object."""
        from scapy.fields import ByteField
        scapy_pkt1 = ScapyBasicOtterPacket1()
        scapy_pkt2 = ScapyBasicOtterPacket1()
        # we clone scapy_pkt1 in order to add a field to the mutable class variable fields_desc
        BOFPacket._clone(scapy_pkt1, "basic_otter_packet_1_clone")
        new_field = ByteField("new_field", 0x42)
        scapy_pkt1.fields_desc.append(new_field)
        # We make sure that scapy_pkt1.fields_desc is not edited
        self.assertTrue(new_field in scapy_pkt1.fields_desc and \
                        new_field not in scapy_pkt2.fields_desc)

    def test_0602_packet_clone_layers(self):
        """Test that packet cloning preserves layers contents and bindings."""
        scapy_pkt = ScapyBasicOtterPacket1()/ScapyBasicOtterPacket2()/ScapyBasicOtterPacket4()
        BOFPacket._clone(scapy_pkt.getlayer("basic_otter_packet_2"), "basic_otter_packet_2_clone")
        self.assertEqual(bytes(scapy_pkt), bytes(ScapyBasicOtterPacket1())
                         + bytes(ScapyBasicOtterPacket2())
                         + bytes(ScapyBasicOtterPacket4()))
        self.assertEqual(scapy_pkt.__class__(raw(scapy_pkt)).getlayer("basic_otter_packet_2").name,
                         "basic_otter_packet_2")
