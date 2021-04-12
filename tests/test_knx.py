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
    def test_02_04_knxnet_receive(self):
        """Test that received bytes are converted to ``KNX``s."""
        frame = b'\x06\x10\x02\x03\x00\x0e\x08\x01\x00\x00\x00\x00\x00\x00'
        recv = self.knxnet.sr(frame)
        self.assertTrue(isinstance(recv[0], knx.KNX))
