"""unittest for ``bof.packet``

- BOFPacket and BOFPacket child class initialization
- Link between BOFPacket classes and Scapy objects below
- BOFPacket-inherited objects handling and usage
"""

import unittest
from bof.packet import *

class Test01PacketConstruct(unittest.TestCase):
    """Test class for raw BOFPacket initialization.
    BOFPacket are not supposed to be instantiated directly.
    """
    def test_0101_bofpacket_construct(self):
        """Test empty constructor."""
        pkt = BOFPacket()
        self.assertEqual(pkt.name, "BOFPacket")
    def test_0102_bofpacket_child_construct(self):
        """Test that we can build an object inheriting from BOFPacket."""
        class OtterPacket(BOFPacket):
            pass
        pkt = OtterPacket()
        self.assertEqual(pkt.name, "OtterPacket")

class Test02ScapyLayers(unittest.TestCase):
    """Test class to make sure that we access Scapy layer content."""
    def test_0201_bofpacket_scapylayer_integrated(self):
        """Test that we can build BOFPacket from layer in scapy library."""
        from scapy.contrib import modbus
        class Modbus(BOFPacket):
            def __init__(self):
                self.scapy_pkt = modbus.ModbusADURequest()
        modbus_pkt = Modbus()
        self.assertEqual(modbus_pkt.name, "ModbusADU")
    def test_0202_bofpacket_scapylayer_standalone(self):
        """Test that we can build BOFPacket from layer as standalone file.
        The standalone file shall have a protocol written with scapy format.
        """
        from bof.layers.raw_scapy import knx
        class KNX(BOFPacket):
            def __init__(self):
                self.scapy_pkt = knx.KNXnetIP()
        knx_pkt = KNX()
        self.assertEqual(knx_pkt.scapy_pkt.name, "KNXnet/IP")
    def test_0203_bofpacket_scapylayer_addpayload_base_scapy(self):
        """Test that we can add a Scapy layer as a payload for a BOFPacket.
        """
        from scapy.layers.inet import TCP
        from scapy.contrib.modbus import ModbusADURequest
        # we want ModbusADURequest as payload for TCP, which are bound by default in Scapy
        pkt = BOFPacket()
        pkt.scapy_pkt = TCP()
        pkt.add_payload(ModbusADURequest())
        # TODO: see how to check for correct packet construction (ie : show2..)
    def test_0204_bofpacket_scapylayer_addpayload_base_bof(self):
        """Test that we can add a BOFPacket as payload for another BOFPacket.
        """
        from scapy.layers.inet import TCP
        from scapy.contrib.modbus import ModbusADURequest
        # we want ModbusADURequest as payload for TCP, which are bound by default in Scapy
        pkt = BOFPacket()
        pkt.scapy_pkt = TCP()
        pkt.add_payload(ModbusADURequest())
        # TODO: see how to check for correct packet construction (ie : show2..)
    def test_0205_bofpacket_scapylayer_addpayload_automatic_scapy(self):
        """Test that we can add an unbound Scapy packet as payload and automatically perform the binding.
        """
        from scapy.layers.inet import TCP
        from scapy.contrib.modbus import ModbusADURequest
        # we want TCP as payload for ModbusADURequest, which are not bound by default in Scapy
        pkt = BOFPacket()
        pkt.scapy_pkt = ModbusADURequest()
        pkt.add_payload(TCP(), automatic_binding=True)
        # TODO: see how to check for correct packet construction (ie : show2..)
        def test_0206_bofpacket_scapylayer_addlayer_no_automatic_scapy(self):
        """Test that we can add an unbound Scapy packet as payload on purpose.
        """
        pkt = BOFPacket()
        pkt.scapy_pkt = ModbusADURequest()
        pkt.add_payload(TCP(), automatic_binding=False)
        # TODO: see how to check for correct packet construction (ie : show2..)


class Test02PacketBuiltins(unittest.TestCase):
    """Test class for raw BOFPacket builtin function overload."""
    @classmethod
    def setUpClass(self):
        self.pkt = BOFPacket()

    def test_0301_bofpacket_bytes(self):
        """Test that bytes() prints Scapy packet bytes."""
        self.assertEqual(bytes(self.pkt), b"") # TODO
    def test_0302_bofpacket_len(self):
        """Test that len() prints Scapy packet length."""
        self.assertEqual(len(self.pkt), 0) # TODO
    def test_0302_bofpacket_str(self):
        """Test that str() prints Scapy packet string."""
        self.assertEqual(str(self.pkt), "BOFPacket: BOFPacket")
    def test_0302_bofpacket_iter(self):
        """Test that str() prints Scapy packet fields."""
        self.assertEqual([x.name for x in self.pkt], []) # TODO
