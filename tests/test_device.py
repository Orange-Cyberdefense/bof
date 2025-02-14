"""Unit tests for ``bof.device``.

- BOFDevice base class object
"""

import unittest
from bof import BOFDevice
        
class Test01BOFDevice(unittest.TestCase):
    """Test class to verify that BOFDevice is correctly set."""
    def test_0101_bofdevice_empty(self):
        dev = BOFDevice()
        self.assertIsNone(dev.name)
        self.assertIsNone(dev.ip_address)
    def test_0102_bofdevice_allargs(self):
        dev = BOFDevice(name="a", ip_address="d")
        self.assertEqual(dev.name, "a")
        self.assertEqual(dev.ip_address, "d")
    def test_0103_bofdevice_partial(self):
        dev = BOFDevice(ip_address="c")
        self.assertIsNone(dev.name)
        self.assertEqual(dev.ip_address, "c")
    def test_0104_bofdevice_unknown(self):
        dev = BOFDevice(banane="e")
        self.assertIsNone(dev.name)
        self.assertEqual(dev.banane, "e")
    def test_0105_bofdevice_assignexists(self):
        dev = BOFDevice()
        dev.ip_gateway = "f"
        self.assertEqual(dev.ip_gateway, "f")
    def test_0106_bofdevice_assignnoexists(self):
        dev = BOFDevice()
        dev.parrot = "g"
        self.assertEqual(dev.parrot, "g")
    def test_0107_bofdevice_title(self):
        dev = BOFDevice(name="h", ip_address="i")
        self.assertEqual(dev.title(dev.name), "Name")
        self.assertEqual(dev.title(dev.ip_address), "IP address")
    def test_0108_bofdevice_notitle(self):
        dev = BOFDevice(name="j", mouflon="k")
        self.assertEqual(dev.title(dev.name), "Name")
        self.assertEqual(dev.title(dev.mouflon), "mouflon")
