"""Unit tests for ``bof.base``.

- Module and submodule imports
- Exceptions
- Logging
- String manipulation
"""

import unittest

class Test01Import(unittest.TestCase):
    """Test class for BOF module and submodules imports."""
    def test_0101_import_bof(self):
        """Test should not raise ImportError"""
        import bof
    def test_0102_import_bof_submodules(self):
        """Test should not raise ImportError"""
        from bof import base

import bof

class Test02Exceptions(unittest.TestCase):
    """Test class for BOFException error handling."""
    def test_0201_raise_boferrors(self):
        with self.assertRaises(bof.BOFError):
            raise bof.BOFError("Base error")
        with self.assertRaises(bof.BOFLibraryError):
            raise bof.BOFLibraryError("Library error")
        with self.assertRaises(bof.BOFNetworkError):
            raise bof.BOFNetworkError("Network error")
        with self.assertRaises(bof.BOFProgrammingError):
            raise bof.BOFProgrammingError("Programming error")

class Test03Logging(unittest.TestCase):
    """Test class for logging features."""
    def test_0301_enable_logging(self):
        """Test that the logging boolean is set to ``True`` when function
        ``enable_logging()`` is called. The global variable tested is not
        supposed to be retrieved this way by final users.
        """
        bof.enable_logging()
        self.assertTrue(bof.base._LOGGING_ENABLED)
    def test_0302_disable_logging(self):
        """Test that the logging boolean is set to ``False`` when function
        ``disable_logging()`` is called. The global variable tested is not
        supposed to be retrieved this way by final users.
        """
        bof.disable_logging()
        self.assertFalse(bof.base._LOGGING_ENABLED)

class Test04StringManipulation(unittest.TestCase):
    """Test class for string manipulation functions."""
    def test_0401_to_property(self):
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
