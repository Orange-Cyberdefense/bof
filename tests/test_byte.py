"""unittest for ``bof.byte``.

- Byteorder settings
- Byte conversion to and from ints
- Byte array resizing
"""
from sys import path
path.append('../')
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




class Test05BitListIntConversion(unittest.TestCase):
    """Test class for bits transformation to int"""
    @classmethod
    def setUpClass(self):
        bof.set_byteorder('big')
    def test_01_int_to_bits_and_back(self):
        """Test conversion from int to bit list, and from bit list to int."""
        value = 19
        size = 8
        result = bof.bit_list_to_int(bof.int_to_bit_list(value, size))
        self.assertEqual(19, result)
    def test_02_int_to_bits_and_back_slices(self):
        """Test conversion from int to bits list, and back, with size reduction."""
        value = 255
        result = bof.bit_list_to_int(bof.int_to_bit_list(value, 7))
        self.assertEqual(127, result)
    def test_03_int_to_bits_and_back_little_endian(self):
        """Test conversion from int to bit list, and from bit list to int in little endian."""
        value = 19
        size = 8

        list_result = bof.int_to_bit_list(value, size, byteorder='little') 
        result = bof.bit_list_to_int(list_result, byteorder='little')
        self.assertEqual(19, result)
    def test_04_int_to_bits_and_back_wrong_endianess(self):
        """Test conversion from int to bit list and back, with the wrong byteorder."""
        value = 19
        size = 8
        list_result = bof.int_to_bit_list(value, size, byteorder='big')
        result = bof.bit_list_to_int(list_result, byteorder='little')
        self.assertNotEqual(19, result)
    def test_05_int_to_bits_invalid_endianess(self):
        """Test conversion from int to bit list with an invalid byteorder."""
        value = 19
        with self.assertRaises(bof.BOFProgrammingError):
            bof.int_to_bit_list(2, byteorder='frite')
    def test_06_bits_to_int_invalid_endianess(self):
        """Test conversion from bit list to int with an invalid byteorder"""
        value = 19
        with self.assertRaises(bof.BOFProgrammingError):
            bof.bit_list_to_int(bof.int_to_bit_list(2), byteorder='frite')


class Test06BytesIpv4Conversion(unittest.TestCase):
    """Test class for bytes conversion to IPV4"""
    @classmethod
    def setUpClass(self):
        bof.set_byteorder('big')
    def test_01_ipv4_to_bytes_and_back(self):
        """Test conversion from ipv4 to bYtes, and from bytes to ipv4."""
        ip = "127.0.0.1"
        self.assertEqual(bof.to_ipv4(bof.from_ipv4(ip)), "127.0.0.1")
    
class Test07BytesMacConversion(unittest.TestCase):
    """Test class for bytes conversion to mac address."""
    @classmethod
    def setUpClass(self):
        bof.set_byteorder('big')
    def test_01_mac_to_bytes(self):
        """Test conversion mac address to bytes."""
        mac = "AB:5C:DF:AA:A2:FC"
        result = bof.from_mac(mac)
        self.assertEqual(b'\xAB\x5C\xDF\xAA\xA2\xFC', result.upper())
    def test_02_bytes_to_mac(self):
        """Test conversion bytes to mac address."""
        byte = b'\xAB\x5C\xDF\xAA\xA2\xFC'
        result = bof.to_mac(byte)
        self.assertEqual("AB:5C:DF:AA:A2:FC".upper(),result.upper())
    def test_03_bytes_to_mac_and_back(self):
        """Test conversion mac address to bytes and back."""
        mac = "AB:5C:DF:AA:A2:FC"
        result = bof.to_mac(bof.from_mac("AB:5C:DF:AA:A2:FC"))
        self.assertEqual(mac.upper(), result.upper())
    def test_04_mac_to_bytes_less_6_bytes(self):
        """Test conversion mac address to bytes with less than 6 bytes."""
        mac = "AB:5C"
        result = bof.from_mac(mac)
        self.assertEqual(b'\xAB\x5C', result)
    def test_05_bytes_to_mac_less_6_bytes(self):
        """Test conversion bytes to mac address with less than 6 bytes."""
        result = bof.to_mac(b'\xAB\x5C')
        self.assertEqual("AB:5C".upper(),result.upper())

class Test07BytesMacConversion(unittest.TestCase):
    """Test class for bytes conversion to mac address."""
    @classmethod
    def setUpClass(self):
        bof.set_byteorder('big')
    def test_01_knx_individual_to_bytes(self):
        """Test that we can convert a KNX address with format X.Y.Z"""
        self.assertEqual(bof.byte.from_knx("15.15.255"), b"\xff\xff")
    def test_02_bytes_to_knx_individual(self):
        """Test that we can convert bytes to X.Y.Z"""
        self.assertEqual(bof.byte.to_knx(b"\x11\x02"), "1.1.2")
    def test_03_knx_group_to_bytes(self):
        """Test that we can convert KNX address with format X/Y/Z"""
        self.assertEqual(bof.byte.from_knx("1/1/1"), b"\x09\x01")
    def test_02_bytes_to_knx_group(self):
        """Test that we can convert bytes to X/Y/Z"""
        self.assertEqual(bof.byte.to_knx(b"\x09\xff", group=True), "1/1/255")

if __name__ == '__main__':
    unittest.main()
