"""unittest for Profinet DCP implementation ``bof.layers.profinet``"""

import unittest
from ipaddress import IPv4Address
from scapy.layers.l2 import Ether
from scapy.contrib.pnio_dcp import DCP_SERVICE_ID, DCP_SERVICE_TYPE

from bof import BOFProgrammingError
from bof.layers import profinet

class Test01PNDCPPacket(unittest.TestCase):
    """Test class for PNDCP packet create."""
    def test_0101_profinet_packet_create_identify(self):
        """Test that we can create a PNDCP multicast packet."""
        pkt = profinet.create_identify_packet()
        self.assertEqual(DCP_SERVICE_ID[pkt["ProfinetDCP"].service_id],
                         "Identify")
        self.assertEqual(DCP_SERVICE_TYPE[pkt["ProfinetDCP"].service_type],
                         "Request")

class Test02LLDPSend(unittest.TestCase):
    """Test class for PNDCP packet send."""
    def test_0201_pndcp_packet_send_default(self):
        """Test that nothing wrong happens when sending packet."""
        with self.assertRaises(BOFProgrammingError): # Test not run as sudo
            profinet.send_identify_request()

class Test03LLDPDevice(unittest.TestCase):
    """Test class for LLDP device objects."""
    def test_0301_pndcp_device_raise(self):
        """Test that we cannot create a PNDCP device with request and not response."""
        pkt = profinet.create_identify_packet()
        with self.assertRaises(BOFProgrammingError):
            device = profinet.ProfinetDevice(pkt)
