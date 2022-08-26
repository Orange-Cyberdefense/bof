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
        self.assertIsNone(dev.description)
        self.assertIsNone(dev.mac_address)
        self.assertIsNone(dev.ip_address)
    def test_0102_bofdevice_allargs(self):
        dev = BOFDevice("a", "b", "c", "d")
        self.assertEqual(dev.name, "a")
        self.assertEqual(dev.description, "b")
        self.assertEqual(dev.mac_address, "c")
        self.assertEqual(dev.ip_address, "d")
    def test_0103_bofdevice_partial(self):
        dev = BOFDevice(mac_address="c")
        self.assertIsNone(dev.name)
        self.assertIsNone(dev.description)
        self.assertEqual(dev.mac_address, "c")
        self.assertIsNone(dev.ip_address)
