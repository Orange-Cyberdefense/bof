"""unittest for ``bof.network``.

- UDP/TCP connection
- UDP/TCP packet exchange (send/receive)
"""

import unittest
import bof

from time import sleep
from subprocess import Popen

UDP_ECHO_SERVER_CMD = "ncat -e /bin/cat -k -u -l 13671"
TCP_ECHO_SERVER_CMD = "ncat -e /bin/cat -k -t -l 23671"

#-----------------------------------------------------------------------------#
# UDP                                                                         #
#-----------------------------------------------------------------------------#

class Test01UDPConnection(unittest.TestCase):
    """Test class for raw UDP connection features.
    UDP connection classes are not supposed to be instantiated directly.
    """
    def test_0101_udp_instantiate(self):
        """Test correct BOF UDP object instantiation."""
        udp = bof.UDP()
    def test_0102_udp_connect(self):
        """Test regular UDP connection."""
        udp = bof.UDP()
        udp.connect("localhost", 13671)
        self.assertEqual(udp._address[0], '127.0.0.1')
        udp.disconnect()
    def test_0103_udp_connect_bad_addr(self):
        """Test error handling for bad address."""
        udp = bof.UDP()
        with self.assertRaises(bof.BOFNetworkError):
            udp.connect("invalid", 13671)
    def test_0104_udp_connect_bad_port(self):
        """Test error handling for bad port."""
        udp = bof.UDP()
        with self.assertRaises(bof.BOFNetworkError):
            udp.connect("localhost", 666666)

class Test02UDPExchange(unittest.TestCase):
    """Test class for UDP datagram exchange.
    Prerequisites: UDP class instantiated, connect and disconnect OK.
    """
    @classmethod
    def setUpClass(self):
        self.udp = bof.UDP()
        self.echo_server = Popen(UDP_ECHO_SERVER_CMD.split())
    def setUp(self):
        self.udp.connect("localhost", 13671)
    def tearDown(self):
        self.udp.disconnect()
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0201_udp_send_str_bytes(self):
        """Test sending data as string and bytes in a UDP datagram.
        We can't assert anything as we don't get a return, but exception
        is raised if format or connection are not ok.
        """
        self.udp.send("test_send")
        self.udp.send(b'\x06\x10\x02\x03')
    def test_0202_udp_send_receive(self):
        """Test that bytes sent in UDP datagram are echoed by the echo server.
        Exception raised if format or connection are not ok.
        """
        result, _ = self.udp.send_receive("test_send_receive", timeout=5)
        self.assertEqual(result.decode('utf-8'), "test_send_receive")
        result, _ = self.udp.sr("test_sr", timeout=5)
        self.assertEqual(result.decode('utf-8'), "test_sr")
    def test_0203_send_receive_timeout(self):
        """Test that a timeout is triggered when no packet is received."""
        udp = bof.UDP()
        udp.connect("localhost", 13672)
        with (self.assertRaises(bof.BOFNetworkError)):
            result, _ = udp.send_receive("test_send_receive", timeout=0.1)
        udp.disconnect()
    def test_0204_multicast_error_handling(self):
        """Test that multicast request parameters are handled correctly."""
        with (self.assertRaises(bof.BOFProgrammingError)):
            bof.UDP.multicast(b"", 1)
        with (self.assertRaises(bof.BOFProgrammingError)):
            bof.UDP.multicast(b"", ("192.168.1.252", -4))
        bof.UDP.multicast("str", ("192.168.1.252", 40000))

    def test_0205_broadcast_error_handling(self):
        """Test that broadcast request parameters are handled correctly."""
        with (self.assertRaises(bof.BOFProgrammingError)):
            bof.UDP.broadcast(b"", 1)
        with (self.assertRaises(bof.BOFProgrammingError)):
            bof.UDP.broadcast(b"", ("192.168.1.252", -4))
        bof.UDP.broadcast("str", ("192.168.1.252", 40000))
            
#-----------------------------------------------------------------------------#
# TCP                                                                         #
#-----------------------------------------------------------------------------#

class Test03TCPConnection(unittest.TestCase):
    """Test class for raw TCP connection features.  
    TCP connection classes are not supposed to be instantiated directly.
    """
    @classmethod
    def setUpClass(self):
        self.echo_server = Popen(TCP_ECHO_SERVER_CMD.split())
        sleep(0.5) # Waiting for TCP handshake
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0301_tcp_instantiate(self):
        """Test correct BOF TCP object instantiation."""
        tcp = bof.TCP()
    def test_0302_tcp_connect(self):
        """Test regular TCP connection."""
        tcp = bof.TCP()
        tcp.connect("localhost", 23671)
        self.assertEqual(tcp.source[0], '127.0.0.1')
        tcp.disconnect()
    def test_0303_tcp_connect_bad_addr(self):
        """Test error handling for bad address."""
        tcp = bof.TCP()
        with self.assertRaises(bof.BOFNetworkError):
            tcp.connect("invalid", 23671)
    def test_0304_tcp_connect_bad_port(self):
        """Test error handling for bad port."""
        tcp = bof.TCP()
        with self.assertRaises(bof.BOFNetworkError):
            tcp.connect("localhost", 666666)

class Test04TCPExchange(unittest.TestCase):
    """Test class for TCP packet exchange.
    Prerequisites: TCP class instantiated, connect and disconnect OK.
    """
    @classmethod
    def setUpClass(self):
        self.tcp = bof.TCP()
        self.echo_server = Popen(TCP_ECHO_SERVER_CMD.split())
        sleep(0.5) # Waiting for TCP handshake
    def setUp(self):
        self.tcp.connect("localhost", 23671)
    def tearDown(self):
        self.tcp.disconnect()
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0401_tcp_send_str_bytes(self):
        """Test sending data as string and bytes in a TCP packet."""
        self.tcp.send("test_send")
        self.tcp.send(b'\x06\x10\x02\x03')
    def test_0402_tcp_send_receive(self):
        """Test that bytes sent in TCP packet are echoed by the echo server.
        Exception raised if format or connection are not ok.
        """
        result, _ = self.tcp.send_receive("test_send_receive", timeout=5)
        self.assertEqual(result.decode('utf-8'), "test_send_receive")
        result, _ = self.tcp.sr("test_sr", timeout=5)
        self.assertEqual(result.decode('utf-8'), "test_sr")
