"""unittest for ``bof.network``.

- UDP connection
- UDP packet exchange (send/receive)
"""

import unittest
import bof

class Test01UDPConnection(unittest.TestCase):
    """Test class for raw UDP connection features. Not real-world case: UDP
    connection classes are not supposed to be instantiated directly.
    """
    def test_01_udp_instantiate(self):
        """Test correct BOF UDP object instantiation."""
        udp = bof.UDP()
    def test_02_udp_connect(self):
        """Test regular UDP connection."""
        udp = bof.UDP()
        udp.connect("localhost", 13671)
        self.assertEqual(udp.source[0], '127.0.0.1')
        udp.disconnect()
    def test_03_udp_connect_bad_addr(self):
        """Test error handling for bad address."""
        udp = bof.UDP()
        with self.assertRaises(bof.BOFNetworkError):
            udp.connect("invalid", 13671)
    def test_04_udp_connect_bad_port(self):
        """Test error handling for bad port."""
        udp = bof.UDP()
        with self.assertRaises(bof.BOFNetworkError):
            udp.connect("localhost", 666666)

class Test02UDPExchange(unittest.TestCase):
    """Test class for UDP datagram exchange.
    Prerequisites: UDP class instantiated, connect and disconnect OK.
    Uses a UDP echo server: `python2 tests/simple_udp_echo_server.py`.
    """
    @classmethod
    def setUpClass(self):
        self.udp = bof.UDP()
    def setUp(self):
        self.udp.connect("localhost", 13671)
    def test_01_udp_send_str(self):
        """Test sending data as string in a UDP datagram. We can't assert
        anything as we don't get a return, but exception is raised if format or 
        connection are not ok.
        """
        self.udp.send("test_send")
    def test_02_udp_send_bytes(self):
        """Test sending bytes in UDP datagram. No return value to assert but 
        exception is raised if format or connection are not ok.
        """
        self.udp.send(b'\x06\x10\x02\x03')
    def test_03_udp_send_receive(self):
        """Test that bytes sent in UDP datagram are correctly echoed by the
        remote echo server we connected to. Exception raised if format or
        connection are not ok.
        """
        result, _ = self.udp.send_receive("test_send_receive", timeout=10)
        self.assertEqual(result.decode('utf-8'), "test_send_receive")
    def test_04_send_receive_timeout(self):
        """Test that a timeout is triggered when no packet is received."""
        udp = bof.UDP()
        udp.connect("localhost", 12345)
        with (self.assertRaises(bof.base.BOFNetworkError)):
            result, _ = udp.send_receive("test_send_receive", timeout=0.5)
        udp.disconnect()
    def tearDown(self):
        self.udp.disconnect()

if __name__ == '__main__':
    unittest.main()
