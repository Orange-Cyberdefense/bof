"""unittest for ``bof.knx``.

- KNX device object
- Upper-level KNX device discovery
"""

import unittest
from bof import knx, BOFProgrammingError

BOIBOITE = "192.168.1.10"

class Test01DeviceDiscovery(unittest.TestCase):
    """Test class for basic KNX frame creation and usage."""
    def test_01_knxdiscover(self):
        device = knx.discover(BOIBOITE)
        self.assertTrue(isinstance(device, knx.KnxDevice))
    def test_02_knxmultidiscover(self):
        devices = knx.discover("192.168.1.1,192.168.1.10")
        self.assertTrue(isinstance(devices, list))
        self.assertTrue(isinstance(devices[0], knx.KnxDevice))
    @unittest.skip("slow")
    def test_03_knxrangediscover(self):
        devices = knx.discover("192.168.1.0/24")
        self.assertTrue(isinstance(devices, list))
        self.assertTrue(isinstance(devices[0], knx.KnxDevice))
        self.assertEqual(devices[0].address, "192.168.1.10")
        self.assertEqual(devices[0].port, 3671)
    def test_04_knxwrongdiscover(self):
        device = knx.discover("192.168.1.1")
        self.assertEqual(device, None)
    def test_05_knxwrongdiscover2(self):
        with self.assertRaises(BOFProgrammingError):
            device = knx.discover("hi")
    def test_06_knxwrongmultidiscover(self):
        with self.assertRaises(BOFProgrammingError):
            devices = knx.discover("192.168.1.1,hi")
    def test_07_knxwrongrangediscover(self):
        with self.assertRaises(BOFProgrammingError):
            devices = knx.discover("192.168.1.1/61")

class Test02DeviceCreate(unittest.TestCase):
    """Test class for basic KNX frame creation and usage."""
    def test_01_knxdevice_create(self):
        device = knx.KnxDevice(name="toto", address="192.168.1.1", port=3671)
        self.assertEqual(device.name, "toto")
        self.assertEqual(device.address, "192.168.1.1")
        self.assertEqual(device.port, 3671)
    def test_02_knxdevice_wrongcreate(self):
        with self.assertRaises(BOFProgrammingError):
            device = knx.KnxDevice(name=1, address="192.168.1.1", port=3671)
        with self.assertRaises(BOFProgrammingError):
            device = knx.KnxDevice(name="toto", address="192.168.1.263", port=3671)
        with self.assertRaises(BOFProgrammingError):
            device = knx.KnxDevice(name="toto", address="192.168.1.1", port="poulet")
    def test_02_knxdevice_bytecreate(self):
        device = knx.KnxDevice(name=b"toto", address=b"192.168.1.1", port=b"\x10\x10")
        self.assertEqual(device.name, "toto")
        self.assertEqual(device.address, "192.168.1.1")
        self.assertEqual(device.port, 4112)
