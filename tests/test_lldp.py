"""unittest for LLDP implementation ``bof.layers.lldp``"""

import unittest
from ipaddress import IPv4Address
from scapy.layers.l2 import Ether

from bof import BOFProgrammingError
from bof.layers import lldp

class Test01LLDPPacket(unittest.TestCase):
    """Test class for LLDP packet create."""
    def test_0101_lldp_packet_create_default(self):
        """Test that we can create a LLDP multicast packet with default param."""
        pkt = lldp.create_packet()
        self.assertEqual(pkt["LLDPDUSystemName"].system_name.decode('utf-8'),
                         lldp.DEFAULT_PARAM["system_name"])
        self.assertEqual(pkt["LLDPDUSystemDescription"].description.decode('utf-8'),
                         lldp.DEFAULT_PARAM["system_desc"])
        self.assertEqual(IPv4Address(pkt["LLDPDUManagementAddress"].management_address),
                         IPv4Address(lldp.DEFAULT_PARAM["management_address"]))
        self.assertEqual(pkt["LLDPDUChassisID"].id.decode('utf-8'),
                         lldp.DEFAULT_PARAM["chassis_id"])
        self.assertEqual(pkt["LLDPDUPortID"].id.decode('utf-8'),
                         lldp.DEFAULT_PARAM["port_id"])
        self.assertEqual(pkt["LLDPDUPortDescription"].description.decode('utf-8'),
                         lldp.DEFAULT_PARAM["port_desc"])

    def test_0102_lldp_packet_create_raise(self):
        "Test that create packet raises BOFProgrammingError if param wrong"
        with self.assertRaises(BOFProgrammingError):
            lldp.create_packet({"chassis_id": "nul"})

class Test02LLDPSend(unittest.TestCase):
    """Test class for LLDP packet send."""
    def test_0201_lldp_packet_send_default(self):
        """Test that nothing wrong happens when sending packet."""
        with self.assertRaises(BOFProgrammingError): # Test not run as sudo
            lldp.send_multicast()
    def test_0202_lldp_packet_send_custom_pkt(self):
        """Test that nothing wrong happens when sending packet."""
        with self.assertRaises(BOFProgrammingError): # Test not run as sudo
            pkt = Ether(type=0x88cc, dst=lldp.MULTICAST_MAC)/lldp.create_packet()
            lldp.send_multicast(pkt)

class Test03LLDPDevice(unittest.TestCase):
    """Test class for LLDP device objects."""
    def test_0301_lldp_device_ether(self):
        """Test that we correctly create a LLDPDevice object with Ether."""
        pkt = Ether(type=0x88cc, src=lldp.MULTICAST_MAC)/lldp.create_packet()
        device = lldp.LLDPDevice(pkt)
        self.assertEqual(device.name, lldp.DEFAULT_PARAM["system_name"])
        self.assertEqual(device.description, lldp.DEFAULT_PARAM["system_desc"])
        self.assertEqual(device.mac_address, lldp.MULTICAST_MAC)
        self.assertEqual(device.ip_address,
                         IPv4Address(lldp.DEFAULT_PARAM["management_address"]))
        self.assertEqual(device.chassis_id, lldp.DEFAULT_PARAM["chassis_id"])
        self.assertEqual(device.port_id, lldp.DEFAULT_PARAM["port_id"])
        self.assertEqual(device.port_desc, lldp.DEFAULT_PARAM["port_desc"])
