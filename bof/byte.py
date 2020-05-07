"""Byte conversion and management functions. Available functions:

- Resize byte arrays to bigger, or truncate to smaller
- Byte conversion to and from integers
- Byte conversion to and from IPv4 strings

.. note:: The default byteorder used is big endian but it can be changed using
          function ``set_byteorder()`` with either ``"little"`` or ``"big"``
          as first parameter.
"""

from .base import BOFProgrammingError
from ipaddress import IPv4Address

__DEFAULT_BYTEORDER = 'big'
_BYTEORDER = __DEFAULT_BYTEORDER

def set_byteorder(byteorder:str) -> None:
    """Changes default byte order to use is byte conversion functions.
    
    :param byteorder: Accepts two values: ``big`` for big endian (default) or
                      ``little`` for little endian
    :raises BOFProgrammingError: If ``byteorder`` is invalid.

    Example::

        set_byteorder(byteorder:str) -> None
    """
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    global _BYTEORDER
    _BYTEORDER = byteorder


def get_size(array) -> int:
    """Gives the number of bytes the parameter ``array`` fits into.

    :param array: Object tested for size. Can have type int or bytes.
    :raises BOFProgrammingError: If ``array`` is not an int or a bytearray.
    """
    if isinstance(array, bytes):
        return len(array)
    if isinstance(array, int):
        return ((array.bit_length() + 7) // 8)
    raise BOFProgrammingError("get_size expects bytes or int")

def resize(array:bytes, size:int, byteorder:str=None) -> bytes:
    """Resize a byte array to the expected ``size``.

    If `size` is bigger than ``array``'s actual size, ``array`` is padded. If
    ``size`` is smaller, the value of ``array`` is truncated. Padding or
    truncation outcomes change according to ``byteorder``. If ``byteorder`` is
    not set, the global ``byteorder`` value will be used (set with
    ``set_byteorder()``).

    :param array: Byte array to resize.
    :param size: The expected size of the byte array after padding/truncation.
    :returns: The resized byte array.

    Example::

        >>> x = bof.byte.from_int(1234)
        >>> x = bof.byte.resize(x, 1)
        >>> x
        b'\xd2'
        >>> x = bof.byte.resize(x, 4)
        >>> x
        b'\x00\x00\x00\xd2'
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if size < len(array):
        return array[len(array)-size:] if byteorder == 'big' else array[:size]
    if size > len(array):
        padding = []
        for _ in range(size - len(array)):
            padding += [b'\x00']
        padding = b''.join(padding)
        return padding + array if byteorder == 'big' else array + padding
    return array

def from_int(value:int, size:int=0, byteorder:str=None) -> bytes:
    """Converts an integer to a bytearray.

    :param value: The integer value to convent to a byte or a byte array.
    :param size: If set, the bytearray will be of the specified size.
    :param byteorder: If set, the conversion will rely on the specified
                      byteorder. Otherwise, global ``byteorder`` will be used
                      (set with ``set_byteorder()``).
    :returns: The value resized as a bytearray.
    :raises BOFProgrammingError: If ``value`` is not int or ``byteorder`` is
                                 invalid.

    Example::

        >>> bof.byte.from_int(65980)
        b'\x01\x01\xbc'
        >>> bof.byte.from_int(65980, size=8, byteorder='big')
        b'\x00\x00\x00\x00\x00\x01\x01\xbc'
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    if not isinstance(value, int) or not isinstance(size, int):
        raise BOFProgrammingError("Int to bytes expects an int")
    value = value.to_bytes((value.bit_length() + 7) // 8, byteorder)
    if len(value) == 0:
        size = 1
    return resize(value, len(value) if not size else size, byteorder)

def to_int(array:bytes, byteorder:str=None) -> int:
    """Converts a byte array to an integer.

    :param array: Byte array to convert to an integer.
    :param byteorder: Byte order to use. If not set, global ``byteorder`` will
                      be used (set with ``set_byteorder()``).
    :returns: The value of the bytearray converted to an integer.
    :raises BOFProgrammingError: If ``array`` is not bytes or ``byteorder`` is
                                 invalid.

    Example::

        >>> bof.byte.to_int(b'\x01\x01\xbc')
        65980
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    if not isinstance(array, bytes):
        raise BOFProgrammingError("Bytes to int expects bytes")
    return int.from_bytes(array, byteorder)

def from_ipv4(ip:str, size:int=0, byteorder:str=None) -> bytes:
    """Converts a IPv4 string to a bytearray.

    :param ip: IPv4 string with format with format ``"A.B.C.D"``
    :param size: If set, the byte aray will be of the specified size.
    :param byteorder: If not set, global ``byteorder`` will be used (set with
                      ``set_byteorder()``).
    :returns: The IPv4 address as a bytearray (should be on 4 bytes).

    Example::

        value = byte.from_ipv4("127.0.0.1")
    """
    return bytes(map(int, ip.split('.')))

def to_ipv4(array:bytes) -> str:
    """Converts a byte array representing an IPv4 address to a string with
    format "A.B.C.D" (IPv4) using Python's builtin ``ipaddress`` module.

    :param array: Byte array to convert to an IPv4 address (usually 4 bytes :)).
    :returns: The IP address as a string with format ``"A.B.C.D"``
    """
    return str(IPv4Address(array))
