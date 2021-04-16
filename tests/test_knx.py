"""unittest for KNX implementation ``bof.layers.knx``

- KNX UDP connection
- KNX packet exchange (send/receive) and init
- Frame creation and parsing
- Frame fuzzing
"""

import unittest
from subprocess import Popen
from bof.layers import knx
from bof.base import BOFProgrammingError

UDP_ECHO_SERVER_CMD = "ncat -e /bin/cat -k -u -l 3671"

class Test01KNXConnection(unittest.TestCase):
    """Test class for KNX connection features."""
    @classmethod
    def setUpClass(self):
        self.echo_server = Popen(UDP_ECHO_SERVER_CMD.split())
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0101_knxnet_instantiate(self):
        knxnet = knx.KNXnet()
    def test_0102_knxnet_connect(self):
        knxnet = knx.KNXnet()
        knxnet.connect("localhost")
        self.assertEqual(knxnet.source_address, "127.0.0.1")
        knxnet.disconnect()

class Test02KNXExchange(unittest.TestCase):
    """Test class for KNX datagram exchange.
    Prerequisites: KNXnet class instantiated, connect and disconnect OK.
    """
    @classmethod
    def setUpClass(self):
        self.knxnet = knx.KNXnet()
        self.echo_server = Popen(UDP_ECHO_SERVER_CMD.split())
    def setUp(self):
        self.knxnet.connect("localhost")
    def tearDown(self):
        self.knxnet.disconnect()
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0201_knxnet_send_knxpacket(self):
        """Test that we can send frames in BOF format."""
        frame_bof = knx.KNXPacket()
        sent = self.knxnet.send(frame_bof)
        self.assertEqual(sent, 6)
    def test_0202_knxnet_send_knxpacket(self):
        """Test that we can send frames in Scapy format."""
        from bof.layers.raw_scapy.knx import KNX, KNXDescriptionRequest
        frame_sca = KNX()/KNXDescriptionRequest()
        recv = self.knxnet.send(frame_sca)
        self.assertEqual(recv, 14)
    def test_0203_knxnet_send_raw(self):
        """Test that we can send frames in bytes directly."""
        frame = b'\x06\x10\x02\x03\x00\x0e\x08\x01\x00\x00\x00\x00\x00\x00'
        recv = self.knxnet.sr(frame)
        self.assertEqual(bytes(recv[0]), frame)
    def test_0204_knxnet_receive(self):
        """Test that received bytes are converted to ``KNX``s."""
        frame = b'\x06\x10\x02\x03\x00\x0e\x08\x01\x00\x00\x00\x00\x00\x00'
        recv = self.knxnet.sr(frame)
        self.assertTrue(isinstance(recv[0], knx.KNXPacket))

class Test03KNXFrameConstructor(unittest.TestCase):
    """Test class for KNX datagram building using BOF's KNX classes.
    KNX implementation classes inherit from ``BOFPacket`` and make a
    correspondence between BOF content and protocol implementation in Scapy.
    """
    def test0301_knx_empty_packet(self):
        """Test that we can instantiate an empty KNX packet."""
        frame = knx.KNXPacket()
        header_fields = ['header_length', 'protocol_version',
                        'service_identifier', 'total_length']
        self.assertEqual([x.name for x in frame.fields], header_fields)
    def test0302_knx_req_type_from_construct_dict(self):
        """Test that we can create a KNX packet with its type from a dict."""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        self.assertEqual(frame.service_identifier, 0x0203)
    def test0303_knx_req_type_from_construct_str(self):
        """Test that we can create a KNX packet with its type as a string."""
        frame = knx.KNXPacket(type="DESCRIPTION REQUEST")
        self.assertEqual(frame.service_identifier, 0x0203)
    def test0304_knx_req_type_from_construct_bytes(self):
        """Test that we can create a KNX packet with its type as value in bytes."""
        frame = knx.KNXPacket(type=b"\x02\x03")
        self.assertEqual(frame.type, "DESCRIPTION_REQUEST")
    def test0305_knx_req_type_from_construct_scapy(self):
        """Test that we can create a KNX packet with its type in scapy."""
        from bof.layers.raw_scapy.knx import KNX, KNXDescriptionRequest
        frame = knx.KNXPacket(scapy_pkt=KNX()/KNXDescriptionRequest())
        self.assertEqual(bytes(frame),
                         b'\x06\x10\x02\x03\x00\x0e\x08\x01\x00\x00\x00\x00\x00\x00')
    def test0306_knx_req_type_from_construct_invalid_str(self):
        """Test that we cannot create a KNX packet with invalid type as string."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KNXPacket(type="NUL")
    def test0307_knx_req_type_from_construct_invalid_bytes(self):
        """Test that we cannot create a KNX packet with invalid type as bytes."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KNXPacket(type=b"\x00\x01")
    def test0308_knx_req_type_from_construct_empty(self):
        """Test that we cannot create a KNX packet with empty type."""
        frame = knx.KNXPacket(type="")
        self.assertEqual(frame.service_identifier, None)
    @unittest.skip("Not implemented yet")
    def test_0309_knx_packet_header_attribute(self):
        """Test that we can create KNX packet and set value to a reachable field."""
        frame = knx.KNXPacket(type=knx.SID.description_request, service_identifier=b"\x02\x01")
        self.assertEqual(frame.service_identifier, 0x0203)
    @unittest.skip("Not implemented yet")
    def test_0310_knx_packet_deeper_attribute(self):
        """Test that we can create KNX packet and set value to any field."""
        frame = knx.KNXPacket(type=knx.SID.description_request, ip_address="192.168.1.1")
        self.assertEqual(frame.control_endpoint.ip_address, "192.168.1.1")
        self.assertEqual(frame.ip_address, "192.168.1.1")
    @unittest.skip("Not implemented yet")
    def test_0311_knx_packet_scapy_attribute(self):
        """Test that we can create KNX packet and set a Scapy packet as attr."""
        from bof.layers.raw_scapy.knx import HPAI
        scapy_pkt = HPAI(ip_address="192.168.1.2")
        frame = knx.KNXPacket(type=knx.SID.description_request, control_endpoint=scapy_pkt)
        self.assertEqual(frame.control_endpoint.ip_address, "192.168.1.2")
        self.assertEqual(frame.ip_address, "192.168.1.2")

class Test04FrameAttributes(unittest.TestCase):
    """Test class for KNX objects acess to subpackets a fields with attributes."""
    def test_0401_knx_attr_direct_read(self):
        """Test that we can directly access the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.search_request)
        self.assertEqual(frame.service_identifier, 0x0201)
    @unittest.skip("Not implemented yet")
    def test_0402_knx_attr_direct_read(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNXPacket()
        frame.service_identifier = b"\x02\x01"
        self.assertEqual(frame.service_identifier, b"\x02\x01")
    @unittest.skip("Not implemented yet")
    def test_0403_knx_attr_deeper_read(self):
        """Test that we can directly access the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        self.assertEqual(frame.port, b"\x00\x00")
        self.assertEqual(frame.control_endpoint.port, b"\x00\x00")
    @unittest.skip("Not implemented yet")
    def test_0404_knx_attr_deeper_write(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        frame.ip_address = "192.168.1.1"
        self.assertEqual(frame.control_endpoint.ip_address, "192.168.1.1")
        self.assertEqual(frame.ip_address, "192.168.1.1")
    @unittest.skip("Not implemented yet")
    def test_0405_knx_attr_deeper_write_scapyrejected(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        frame.ip_address = "hi mark!"
        self.assertEqual(frame.control_endpoint.ip_address, "hi mark!")
        self.assertEqual(frame.ip_address, "hi mark!")
