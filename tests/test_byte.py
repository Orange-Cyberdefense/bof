"""unittest for ``bof.byte``.

- Byteorder settings
- Byte conversion to and from ints
- Byte array resizing
"""

import unittest
import bof

class Test01Byteorder(unittest.TestCase):
    """Test class for byteorder use in byte module."""
    def test_01_default_byteorder(self):
        """Test default byteorder global value.
        This value is not supposed to be retrieved this way by final users.
        """
        self.assertEqual(bof.byte._BYTEORDER, 'big')
    def test_02_byteorder_change(self):
        """Test byteorder value change."""
        bof.byte.set_byteorder('little')
        self.assertEqual(bof.byte._BYTEORDER, 'little')
    def test_03_invalid_byteorder(self):
        """Test that byteorder raises ``BOFProgrammingError`` if not little 
        or big
        """
        with self.assertRaises(bof.BOFProgrammingError):
            bof.byte.set_byteorder('frite')

class Test02ByteIntConversion(unittest.TestCase):
    """Test class for byte conversion functions."""
    def test_01_int_big_conversion(self):
        """Test int to byte conversion with big endian."""
        bof.set_byteorder('big')
        x = bof.byte.from_int(65980)
        self.assertEqual(x, b'\x01\x01\xbc')
    def test_02_int_little_conversion(self):
        """Test int to byte conversion with little endian."""
        bof.set_byteorder('little')
        x = bof.byte.from_int(65980)
        self.assertEqual(x, b'\xbc\x01\x01')
    def test_03_int_largersize_conversion(self):
        """Test forced larger size int to byte conversion."""
        x = bof.byte.from_int(65980, size=8, byteorder='big')
        self.assertEqual(x, b'\x00\x00\x00\x00\x00\x01\x01\xbc')
    def test_04_int_invalid_conversion(self):
        """Test invalid conversion from bytes to int of something invalid."""
        with self.assertRaises(bof.BOFProgrammingError):
            bof.byte.from_int('hey!')
    def test_05_int_invalidbyteorder_conversion(self):
        """Test int to byte conversion with invalid byteorder."""
        with self.assertRaises(bof.BOFProgrammingError):
            bof.byte.from_int(2, 'frite')
    def test_06_byte_big_conversion(self):
        """Test big endian-ordered bytes to int conversion."""
        bof.set_byteorder('big')
        x = bof.byte.to_int(b'\x01\x01\xbc')
        self.assertEqual(x, 65980)
    def test_07_byte_little_conversion(self):
        """Test little endian-ordered bytes to int conversion."""
        bof.set_byteorder('little')
        x = bof.byte.to_int(b'\xbc\x01\x01')
        self.assertEqual(x, 65980)
    def test_08_byte_invalidbyteorder_conversion(self):
        """Test bytes to int conversion with invalid byteorder."""
        with self.assertRaises(bof.BOFProgrammingError):
            bof.byte.to_int(2, 'frite')

class Test03ByteResize(unittest.TestCase):
    """Test class for byte array resizing functions."""
    @classmethod
    def setUpClass(self):
        bof.set_byteorder('big')
    def test_01_byte_truncate(self):
        """Test resize bytes to a smaller size."""
        x = bof.byte.from_int(1234)
        x = bof.byte.resize(x, 1)
        self.assertEqual(x, b'\xd2')
    def test_02_byte_expand(self):
        """Test resize bytes to a larger size."""
        x = bof.byte.from_int(1234)
        x = bof.byte.resize(x, 4)
        self.assertEqual(x, b'\x00\x00\x04\xd2')
    def test_03_byte_truncate_expand(self):
        """Test resize bytes to a smaller size then larger."""
        x = bof.byte.from_int(1234)
        x = bof.byte.resize(x, 1)
        x = bof.byte.resize(x, 4)
        self.assertEqual(x, b'\x00\x00\x00\xd2')
        self.assertEqual(bof.byte.to_int(x), 210)

class Test04ByteAndBits(unittest.TestCase):
    """Test class for bit manipulation inside bits."""
    @classmethod
    def setUpClass(self):
        bof.set_byteorder('big')
    def test_01_byte_to_bit_and_back(self):
        field = b"\x10\x00"
        self.assertEqual(bof.byte.from_bit_list(bof.byte.to_bit_list(field)), b'\x10\x00')
    def test_02_slices(self):
        field = bof.byte.to_bit_list(b"\x10\x00")
        size = 4
        value=15
        field[:size] = bof.byte.int_to_bit_list(value)[-size:]
        self.assertEqual(bof.byte.from_bit_list(field), b"\xF0\x00")

if __name__ == '__main__':
    unittest.main()
