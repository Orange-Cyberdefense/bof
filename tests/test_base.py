"""Unit tests for ``bof.base``.

- Dependencies (Make sure that they are installed)
- Module and submodule imports
- Exceptions
- Logging
- String manipulation
"""

import unittest
from packaging import version

class Test01Dependencies(unittest.TestCase):
    """Test class to verify that required dependencies are installed."""
    def test_0101_scapy_import(self):
        """Test that Scapy is installed and that we can import it."""
        import scapy
    def test_0102_scapy_version(self):
        """Test that Scapy version is at least 2.4.3."""
        import scapy
        self.assertTrue(version.parse(scapy.__version__) >= version.parse("2.4.3"))

class Test02Import(unittest.TestCase):
    """Test class for BOF module and submodules imports."""
    def test_0201_import_bof(self):
        """Test should not raise ImportError"""
        import bof
    def test_0202_import_bof_submodules(self):
        """Test should not raise ImportError."""
        from bof import base
        from bof import BOFDevice
    def test_0203_import_bof_layers(self):
        """Test should not raise ImportError."""
        from bof import layers
        from bof.layers import knx
        from bof import knx
    def test_0204_import_bof_layers(self):
        """Test should not raise ImportError."""
        from bof.layers import raw_scapy
        from bof.layers.raw_scapy import knx as knx_scapy
    def test_0205_import_scapy_raw_layers(self):
        """Test that ``from bof import scapy`` is invalid."""    
        with self.assertRaises(ImportError):
            from bof import scapy
        with self.assertRaises(ImportError):
            from bof.scapy import knx as scapy_knx
    def test_0206_import_scapy_direct_content(self):
        """Test that we can import scapy myaers from scapy install."""
        from scapy.contrib import modbus

import bof

class Test03Exceptions(unittest.TestCase):
    """Test class for BOFException error handling."""
    def test_0301_raise_boferrors(self):
        with self.assertRaises(bof.BOFError):
            raise bof.BOFError("Base error")
        with self.assertRaises(bof.BOFLibraryError):
            raise bof.BOFLibraryError("Library error")
        with self.assertRaises(bof.BOFNetworkError):
            raise bof.BOFNetworkError("Network error")
        with self.assertRaises(bof.BOFProgrammingError):
            raise bof.BOFProgrammingError("Programming error")

class Test04Logging(unittest.TestCase):
    """Test class for logging features."""
    def test_0401_enable_logging(self):
        """Test that the logging boolean is set to ``True`` when function
        ``enable_logging()`` is called. The global variable tested is not
        supposed to be retrieved this way by final users.
        """
        bof.enable_logging()
        self.assertTrue(bof.base._LOGGING_ENABLED)
    def test_0402_disable_logging(self):
        """Test that the logging boolean is set to ``False`` when function
        ``disable_logging()`` is called. The global variable tested is not
        supposed to be retrieved this way by final users.
        """
        bof.disable_logging()
        self.assertFalse(bof.base._LOGGING_ENABLED)

class Test05StringManipulation(unittest.TestCase):
    """Test class for string manipulation functions."""
    def test_0501_to_property(self):
        """Test that function to_property replaces all non-alnum character in a
        string with a single underscore.
        """
        self.assertEqual(bof.to_property(""), "")
        self.assertEqual(bof.to_property("abcd1234"), "abcd1234")
        self.assertEqual(bof.to_property("save water"), "save_water")
        self.assertEqual(bof.to_property("!drink..beer!"), "_drink_beer_")
        self.assertEqual(bof.to_property("./!&-1?"), "_1_")
        self.assertEqual(bof.to_property(1), 1)

if __name__ == '__main__':
    unittest.main()
