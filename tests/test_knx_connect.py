"""unittest for ``bof.knx``.

- Submodule import
- KnxNet object instantiation
- KNX communication establishment via UDP
"""

import unittest

class Test01Import(unittest.TestCase):
    """Test class for KNX submodule import."""
    def test_01_import_knx(self):
        """Test import, should not raise ImportError"""
        import bof.knx
    def test_02_import_knx_from(self):
        """Test import, should not raise ImportError"""
        from bof import knx

from bof import knx, BOFNetworkError

class Test02KNXConnection(unittest.TestCase):
    """Test class KNX connection features."""
    def test_01_knx_instantiate(self):
        """Test that BOF object is correctly instantiated."""
        knxnet = knx.KnxNet()
        # TODO: Assert something
    def test_02_knx_connect(self):
        """Test regular KNX connection with no message sent.
        Pass even when no gateway (thx UDP).
        """
        knxnet = knx.KnxNet()
        knxnet.connect("192.168.0.10", init=False)
        knxnet.disconnect()
    def test_03_knx_connect_bad_addr(self):
        """Test error handling for bad address."""
        with self.assertRaises(BOFNetworkError):
            knx.KnxNet().connect("invalid")
    def test_04_knx_connect_bad_port(self):
        """Test error handling for bad port."""
        with self.assertRaises(BOFNetworkError):
            knx.KnxNet().connect("192.168.0.10", 666666)
    @unittest.skip("Response frames not parsed yet")
    def test_05_knx_connect_with_init(self):
        """Test regular KNX connection.
        Sends init packet DescrReq and expects DescrResp from dest.
        """
        knxnet = knx.KnxNet()
        # knxnet.connect("192.168.0.10", 3671)
        knxnet.connect("localhost", 13671)
        datagram = knxnet.receive()
        print(datagram)
        self.assertTrue(isinstance(datagram, knx.KnxFrame))
        knxnet.disconnect()
