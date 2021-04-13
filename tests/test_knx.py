"""unittest for KNX implementation ``bof.layers.knx``

- KNX UDP connection
- KNX packet exchange (send/receive) and init
- Frame creation and parsing
- Frame fuzzing
"""

import unittest
from subprocess import Popen
from bof.layers import knx

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
        frame_bof = knx.KNX() # TODO: Not satisfied with the syntax
        recv = self.knxnet.send(frame_bof)
        self.assertEqual(recv, 6)
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
        self.assertTrue(isinstance(recv[0], knx.KNX))

class Test03KNXFrameConstructor(unittest.TestCase):
    """Test class for KNX datagram building using BOF's KNX classes.
    KNX implementation classes inherit from ``BOFPacket`` and make a
    correspondence between BOF content and protocol implementation in Scapy.
    """
    def test0301_knx_empty_packet(self):
        """Test that we can instantiate an empty KNX packet."""
        frame = knx.KNX()
        header_fields = ['header_length', 'protocol_version',
                        'service_identifier', 'total_length']
        self.assertEqual([x.name for x in frame.fields], header_fields)
    def test0302_knx_req_type(self): # syntax to review
        """Test that we can create a KNX packet with a specific type."""
        frame = knx.KNXDescriptionRequest()
        print([x for x in frame])
        print(frame.fields)
        # TODO
    def test0303_knx_req_type_from_construct(self): # optional
        """Test that we can create a KNX packet with its type in constructor."""
        frame = knx.KNX(type="DESCRIPTION REQUEST") # syntax to review
        # TODO
    def test_0304_knx_packet_header_attribute(self): # syntax to review
        """Test that we can create KNX packet and set value to a reachable field."""
        frame = knx.KNX(service_identifier=b"\x0201")
        # TODO
    def test_0305_knx_packet_deeper_attribute(self): # syntax to review
        """Test that we can create KNX packet and set value to any field."""
        frame = knx.KNXDescriptionRequest(ip_address="oh no.")
        # TODO
    def test_0306_knx_packet_scapy_attribute(self): # syntax to review
        """Test that we can create KNX packet and set a Scapy packet as attr."""
        scapy_pkt = HPAI(ip_address="oh yeah.")
        frame = knx.KNXDescriptionRequest(control_endpoint=scapy_pkt)
        # TODO

class Test04FrameAttributes(unittest.TestCase):
    """Test class for KNX objects acess to subpackets a fields with attributes."""
    def test_0401_knx_attr_direct_read(self):
        """Test that we can directly access the attribute of a packet."""
        frame = knx.KNX()
        self.assertEqual(frame.service_identifier, b"\x00\x00")
    def test_0402_knx_attr_direct_read(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNX()
        frame.service_identifier = b"\x02\x01"
        self.assertEqual(frame.service_identifier, b"\x02\x01")
    def test_0403_knx_attr_deeper_read(self):
        """Test that we can directly access the attribute of a packet."""
        frame = knx.KNX()
        self.assertEqual(frame.port, b"\x00\x00")
        self.assertEqual(frame.control_endpoint.port, b"\x00\x00")
    def test_0404_knx_attr_deeper_write(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNXDescriptionRequest()
        frame.ip_address = "hi mark!"
        self.assertEqual(frame.control_endpoint.ip_address, "hi mark!")
        self.assertEqual(frame.ip_address, "hi mark!")
