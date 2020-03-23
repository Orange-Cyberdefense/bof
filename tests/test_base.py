"""unittest for ``bof.base``.

- Module and submodule imports
- Logging
- JSON file handling
"""

import unittest

class Test01Import(unittest.TestCase):
    """Test class for BOF module and submodules imports."""
    def test_01_import_bof(self):
        """Test should not raise ImportError"""
        import bof
    def test_02_import_bof_submodules(self):
        """Test should not raise ImportError"""
        from bof import base, network, byte

import bof

class Test02Logging(unittest.TestCase):
    """Test class for logging features."""
    def test_01_enable_logging(self):
        """Check that the logging boolean is set to ``True`` when function
        ``enable_logging()`` is called. The global variable tested is not
        supposed to be retrieved this way by final users.
        """
        bof.enable_logging()
        self.assertTrue(bof.base._LOGGING_ENABLED)
    def test_02_disable_logging(self):
        """Check that the logging boolean is set to ``False`` when function
        ``disable_logging()`` is called. The global variable tested is not
        supposed to be retrieved this way by final users.
        """
        bof.disable_logging()
        self.assertFalse(bof.base._LOGGING_ENABLED)

class Test03JSONFiles(unittest.TestCase):
    """Test class for JSON files opening, parsing and handling."""
    def test_01_open_invalid_json(self):
        """Test that an invalid JSON file raises BOFLibraryError."""
        with self.assertRaises(bof.BOFLibraryError):
            bof.load_json("invalid")

if __name__ == '__main__':
    unittest.main()
