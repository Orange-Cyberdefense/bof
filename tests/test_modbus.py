"""unittest for Modbus TCP implementation ``bof.layers.modbus``

- Modbus packet frame creation and parsing
- Modbus TCP connection and packet exchange (send/receive) TODO
- Frame Fuzzing TODO
"""

import unittest

from scapy.contrib.modbus import ModbusADURequest, ModbusPDU01ReadCoilsRequest

from bof import BOFProgrammingError
from bof.layers import modbus

class Test03ModbusFrameConstructor(unittest.TestCase):
    """Test class for Modbus TCP frame building using BOF's Modbus classes.
    Modbus implementation classes inherit from ``ModbusPacket`` and make a
    correspondence between BOF content and protocol implementation in Scapy.
    """
    def test0301_modbus_empty_packet(self):
        """Test that we can create a Modbus TCP frame with no PDU"""
        modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST)
        adu_fields = ['transId', 'protoId', 'len', 'unitId']
        self.assertEqual([x.name for x in modbus_frame.fields], adu_fields)
        self.assertEqual(bytes(modbus_frame), b'\x00\x00\x00\x00\x00\x01\xff')

    def test0302_modbus_empty_packet_invalid_type(self):
        """Test that we cannot create a Modbust TCP frame ith no PDU if no type
        is specified"""
        with self.assertRaises(BOFProgrammingError):
            modbus_frame = modbus.ModbusPacket()

    def test0303_modbus_raw_bytes(self):
        """Test that we can create a Modbus TCP frame from raw bytes"""
        write_single_reg_req_bytes = b'\x01\xf5\x00\x00\x00\x06\x07\x06\x00\x04\x09\xc4'
        modbus_frame = modbus.ModbusPacket(_pkt=write_single_reg_req_bytes,
                                           type=modbus.MODBUS_TYPES.REQUEST)
        adu_fields = ['transId', 'protoId', 'len', 'unitId',
                      'funcCode', 'registerAddr', 'registerValue']
        self.assertEqual([x.name for x in modbus_frame.fields], adu_fields)
        self.assertEqual(bytes(modbus_frame),
                         b'\x01\xf5\x00\x00\x00\x06\x07\x06\x00\x04\x09\xc4')

    def test0304_modbus_raw_bytes_invalid_type(self):
        """Test that we cannot create a Modbus TCP frame from raw bytes if no
        type is specified"""
        write_single_reg_req_bytes = b'\x01\xf5\x00\x00\x00\x06\x07\x06\x00\x04\x09\xc4'
        with self.assertRaises(BOFProgrammingError):
            modbus_frame = modbus.ModbusPacket(_pkt=write_single_reg_req_bytes)

    def test0305_modbus_scapy_packet(self):
        """Test that we can create a Modbus TCP frame from Scapy"""
        scapy_modbus_packet = ModbusADURequest()/ModbusPDU01ReadCoilsRequest()
        modbus_frame = modbus.ModbusPacket(scapy_pkt=scapy_modbus_packet)
        self.assertEqual(bytes(modbus_frame),
                         b'\x00\x00\x00\x00\x00\x06\xff\x01\x00\x00\x00\x01')


    def test0306_modbus_function_int(self):
        """Test that we can create a Modbus TCP frame from function code passed
        as integer"""
        modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function=0x01)
        self.assertEqual(bytes(modbus_frame),
                         b'\x00\x00\x00\x00\x00\x06\xff\x01\x00\x00\x00\x01')

    def test0307_modbus_function_bytes(self):
        """Test that we can create a Modbus TCP frame from function code passed
        as bytes"""
        modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function=b'\x01')
        self.assertEqual(bytes(modbus_frame),
                         b'\x00\x00\x00\x00\x00\x06\xff\x01\x00\x00\x00\x01')

    def test0308_modbus_function_str(self):
        """Test that we can create a Modbus TCP frame from function name passed
        as a string (from MODBUS_FUNCTIONS_CODES)"""
        modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function="Read Coils")
        self.assertEqual(bytes(modbus_frame),
                         b'\x00\x00\x00\x00\x00\x06\xff\x01\x00\x00\x00\x01')

    def test0310_modbus_function_invalid_int(self):
        """Test that we cannot create a modbus TCP frame from invalid function
        code passed as integer"""
        with self.assertRaises(BOFProgrammingError):
            modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                               function=0x42)

    def test0311_modbus_function_invalid_bytes(self):
        """Test that we cannot create a modbus TCP frame from invalid function
        code passed as bytes"""
        with self.assertRaises(BOFProgrammingError):
            modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function=b'\x42')

    def test0312_modbus_function_invalid_str(self):
        """Test that we can create a Modbus TCP frame from invalid function name
        passed as a string (from MODBUS_FUNCTIONS_CODES)"""
        with self.assertRaises(BOFProgrammingError):
            modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function="Invalid Function Name")

    def test0313_modbus_function_invalid_type(self):
        """Test that we cannot create a Modbus TCP frame from function code
        (here passed as integer) if no type is specified"""
        with self.assertRaises(BOFProgrammingError):
            modbus_frame = modbus.ModbusPacket(function=0x01)

    def test0314_modbus_function_empty(self):
        """Test that we can create a Modbus TCP frame with empty function,
        defaulting in a Modbus ADU with no PDU"""
        modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function="")
        adu_fields = ['transId', 'protoId', 'len', 'unitId']
        self.assertEqual([x.name for x in modbus_frame.fields], adu_fields)
        self.assertEqual(bytes(modbus_frame), b'\x00\x00\x00\x00\x00\x01\xff')

    def test0315_modbus_adu_attribtute(self):
        """Test that we can create a Modbus TCP packet and set the value of a
        reachable field"""
        modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function="Read Coils",
                                           protoId=0x42)
        self.assertEqual(modbus_frame.protoId, 0x42)
        self.assertEqual(modbus_frame.scapy_pkt.protoId, 0x42)
        self.assertEqual(bytes(modbus_frame),
                         b'\x00\x00\x00\x42\x00\x06\xff\x01\x00\x00\x00\x01')

    def test0316_modbus_pdu_attribtute(self):
        """Test tjat we can create a Modbus TCP packet and set the value of any
         field"""

        modbus_frame = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST,
                                           function="Read Coils",
                                           startAddr=0x42)
        self.assertEqual(modbus_frame.startAddr, 0x42)
        self.assertEqual(modbus_frame.scapy_pkt.startAddr, 0x42)
        self.assertEqual(bytes(modbus_frame),
                         b'\x00\x00\x00\x00\x00\x06\xff\x01\x00\x42\x00\x01')
