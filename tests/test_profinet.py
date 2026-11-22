"""unittest for Profinet DCP implementation ``bof.layers.profinet``"""

import unittest
from ipaddress import IPv4Address
from scapy.layers.l2 import Ether
from scapy.contrib.pnio import ProfinetIO
from scapy.contrib.pnio_dcp import DCP_SERVICE_ID, DCP_SERVICE_TYPE, \
    DCP_SERVICE_ID_GET, DCP_SERVICE_ID_IDENTIFY, DCP_REQUEST, DCP_RESPONSE, \
    DCP_IDENTIFY_RESPONSE_FRAME_ID, ProfinetDCP, DCPNameOfStationBlock

from bof import BOFProgrammingError
from bof.layers import profinet


def create_dcp_packet(service_id: int, service_type: int) -> ProfinetIO:
    """Create a Profinet DCP packet with given service_id and service_type."""
    return ProfinetIO(frameID=DCP_IDENTIFY_RESPONSE_FRAME_ID)/ProfinetDCP(
        service_id=service_id, service_type=service_type, xid=0x1366b490)

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

    def test_0302_pndcp_device_identify_response_success(self):
        """Test that an identify response success creates a device (no raise)."""
        pkt = create_dcp_packet(DCP_SERVICE_ID_IDENTIFY, DCP_RESPONSE) \
              /DCPNameOfStationBlock(name_of_station=b"device1")
        device = profinet.ProfinetDevice(pkt)
        self.assertEqual(device.protocol, "ProfinetDCP")
        self.assertEqual(device.name, "device1")

    def test_0303_pndcp_device_other_service_id_response_success(self):
        """Test that a response success with another service_id raises."""
        pkt = create_dcp_packet(DCP_SERVICE_ID_GET, DCP_RESPONSE)
        with self.assertRaisesRegex(BOFProgrammingError,
                                    "Expecting an identify response"):
            device = profinet.ProfinetDevice(pkt)

    def test_0304_pndcp_device_other_service_id_request(self):
        """Test that a request with another service_id raises."""
        pkt = create_dcp_packet(DCP_SERVICE_ID_GET, DCP_REQUEST)
        with self.assertRaises(BOFProgrammingError):
            device = profinet.ProfinetDevice(pkt)

    def test_0305_pndcp_device_identify_response_not_supported(self):
        """Test that an identify response with service_type != success raises."""
        pkt = create_dcp_packet(DCP_SERVICE_ID_IDENTIFY, 0x05) # Response - not supported
        with self.assertRaisesRegex(BOFProgrammingError,
                                    "Expecting an identify response"):
            device = profinet.ProfinetDevice(pkt)

    def test_0306_pndcp_device_non_dcp_packet(self):
        """Test that a packet without ProfinetDCP layer does not raise."""
        pkt = Ether(src="aa:bb:cc:dd:ee:ff")
        device = profinet.ProfinetDevice(pkt)
        self.assertEqual(device.mac_address, "aa:bb:cc:dd:ee:ff")
