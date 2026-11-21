"""unittest for LLDP implementation ``bof.layers.lldp``"""

import unittest
from unittest import mock
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
    def test_0203_lldp_send_root_calls_sendp_with_pkt(self):
        """Test that as root, sendp is called with the Ether-wrapped default pkt."""
        with mock.patch("bof.layers.lldp.lldp_functions.geteuid", return_value=0), \
             mock.patch("bof.layers.lldp.lldp_functions.sendp") as mock_sendp:
            sent = lldp.send_multicast()
        mock_sendp.assert_called_once()
        args, kwargs = mock_sendp.call_args
        self.assertEqual(len(args), 1) # single positional arg: the packet
        expected = Ether(type=0x88cc, dst=lldp.MULTICAST_MAC)/lldp.create_packet()
        self.assertEqual(bytes(args[0]), bytes(expected))
        self.assertEqual(args[0]["Ether"].dst, lldp.MULTICAST_MAC)
        self.assertEqual(args[0]["Ether"].type, 0x88cc)
        self.assertIn("LLDPDU", args[0])
        self.assertEqual(kwargs, {"multi": 1, "iface": lldp.DEFAULT_IFACE,
                                  "verbose": False})
        self.assertEqual(bytes(sent), bytes(expected)) # returns the sent packet
    def test_0204_lldp_send_root_custom_pkt_iface_mac(self):
        """Test that as root, a bare LLDPDU pkt is wrapped and sent with custom iface/mac."""
        pkt = lldp.create_packet()
        with mock.patch("bof.layers.lldp.lldp_functions.geteuid", return_value=0), \
             mock.patch("bof.layers.lldp.lldp_functions.sendp") as mock_sendp:
            sent = lldp.send_multicast(pkt, iface="eth9", mac_addr="01:02:03:04:05:06")
        mock_sendp.assert_called_once()
        args, kwargs = mock_sendp.call_args
        expected = Ether(type=0x88cc, dst="01:02:03:04:05:06")/pkt
        self.assertEqual(bytes(args[0]), bytes(expected))
        self.assertEqual(args[0]["Ether"].dst, "01:02:03:04:05:06")
        self.assertEqual(args[0]["Ether"].type, 0x88cc)
        self.assertEqual(kwargs, {"multi": 1, "iface": "eth9", "verbose": False})
        self.assertIs(sent, args[0]) # returns the exact packet sent
    def test_0205_lldp_send_root_pkt_already_ether_not_rewrapped(self):
        """Test that as root, a pkt already containing Ether is sent as-is."""
        pkt = Ether(type=0x88cc, dst="aa:bb:cc:dd:ee:ff")/lldp.create_packet()
        with mock.patch("bof.layers.lldp.lldp_functions.geteuid", return_value=0), \
             mock.patch("bof.layers.lldp.lldp_functions.sendp") as mock_sendp:
            sent = lldp.send_multicast(pkt)
        mock_sendp.assert_called_once()
        args, kwargs = mock_sendp.call_args
        self.assertIs(args[0], pkt) # no double Ether wrapping
        self.assertEqual(args[0]["Ether"].dst, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(kwargs, {"multi": 1, "iface": lldp.DEFAULT_IFACE,
                                  "verbose": False})
        self.assertIs(sent, pkt)
    def test_0206_lldp_send_non_root_raises_and_sendp_not_called(self):
        """Test that as non-root, BOFProgrammingError is raised and sendp not called."""
        with mock.patch("bof.layers.lldp.lldp_functions.geteuid", return_value=1000), \
             mock.patch("bof.layers.lldp.lldp_functions.sendp") as mock_sendp:
            with self.assertRaises(BOFProgrammingError):
                lldp.send_multicast()
            with self.assertRaises(BOFProgrammingError):
                lldp.send_multicast(lldp.create_packet(), iface="eth9")
        mock_sendp.assert_not_called()

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
