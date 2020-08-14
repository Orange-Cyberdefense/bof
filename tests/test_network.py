"""unittest for ``bof.network``.

- UDP/TCP connection
- UDP/TCP packet exchange (send/receive)
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

@unittest.skip("UDP echo server disabled")
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

class Test03TCPConnection(unittest.TestCase):
    """Test class for raw TCP connection features. Not real-world case: TCP
    connection classes are not supposed to be instantiated directly.
    """
    def test_01_tcp_instantiate(self):
        """Test correct BOF TCP object instantiation."""
        tcp = bof.TCP()
    def test_02_tcp_connect_bad_addr(self):
        """Test error handling for bad address."""
        tcp = bof.TCP()
        with self.assertRaises(bof.BOFNetworkError):
            tcp.connect("invalid", 4840)
    def test_03_tcp_connect_bad_port(self):
        """Test error handling for bad port."""
        tcp = bof.TCP()
        with self.assertRaises(bof.BOFNetworkError):
            tcp.connect("localhost", 666666)

@unittest.skip("TCP echo server disabled")
class Test04TCPExchange(unittest.TestCase):
    """Test class for TCP data exchange.
    Prerequisites: TCP class instantiated.
    Uses a TCP echo server: `python3 tests/simple_tcp_echo_server.py`.
    """
    @classmethod
    def setUpClass(self):
        self.tcp = bof.TCP()
    def setUp(self):
        self.tcp.connect("localhost", 4840)
    def tearDown(self):
        self.tcp.disconnect()
    def test_01_tcp_connect(self):
        """Test regular TCP connection."""
        self.assertEqual(self.tcp.source[0], '127.0.0.1')
    def test_02_tcp_send_str(self):
        """Test sending data as string in a using TCP (!= echo). We can't assert
        anything as we don't get a return, but exception is raised if format or 
        connection are not ok.
        """
        self.tcp.send("test_send")
        response, address = self.tcp.receive(timeout=10)
    def test_03_tcp_send_bytes(self):
        """Test sending bytes using TCP (!= echo). No return value to assert but 
        exception is raised if format or connection are not ok.
        """
        self.tcp.send(b'\x1c\xeb\x00\xda')
    def test_04_tcp_send_receive(self):
        """Test that bytes sent using TCP are correctly echoed by the
        remote echo server we connected to. Exception raised if format or
        connection are not ok.
        """
        result, _ = self.tcp.send_receive("test_send_receive", timeout=10)
        self.assertEqual(result.decode('utf-8'), "test_send_receive")
    def test_05_tcp_send_receive_timeout(self):
        """Test that a timeout is triggered when no packet is received in time.
        A server-side dealy is forced by sending the special message ``force_timeout``"""
        with (self.assertRaises(bof.base.BOFNetworkError)):
            result, _ = self.tcp.send_receive("force_timeout", timeout=0.1)

if __name__ == '__main__':
    unittest.main()
