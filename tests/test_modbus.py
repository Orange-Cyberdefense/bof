"""unittest for Modbus TCP implementation ``bof.layers.modbus``

- Modbus packet frame creation and parsing
- Modbus TCP connection and packet exchange (send/receive)
- Frame use-cases / examples TODO
"""

import unittest
from subprocess import Popen
from time import sleep
from types import SimpleNamespace

from scapy.contrib.modbus import ModbusADURequest, ModbusPDU01ReadCoilsRequest

from bof import BOFProgrammingError, BOFDeviceError
from bof.layers import modbus

TCP_ECHO_SERVER_CMD_1 = "ncat -e /bin/cat -k -l 1502"
TCP_ECHO_SERVER_CMD_2 = "ncat -e /bin/cat -k -l 1503"

class Test01ModbusConnection(unittest.TestCase):
    """Test class for Modbus TCP connection features"""
    @classmethod
    def setUpClass(self):
        self.echo_server = Popen(TCP_ECHO_SERVER_CMD_1.split())
        sleep(1)
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0101_modbusnet_instantiate(self):
        modbus_net = modbus.ModbusNet()

    def test_0102_modbusnet_connect(self):
        modbus_net = modbus.ModbusNet()
        modbus_net.connect("127.0.0.1", 1502)
        self.assertEqual(modbus_net.source_address, "127.0.0.1")
        modbus_net.disconnect()

class Test02ModbusExchange(unittest.TestCase):
    """Test class for Modbus TCP exchange.
    Prerequisites: ModbusNet class instantiated, connect and disconnect OK.
    """
    @classmethod
    def setUpClass(self):
        self.modbus_net = modbus.ModbusNet()
        self.echo_server = Popen(TCP_ECHO_SERVER_CMD_2.split())
        sleep(1)
    def setUp(self):
        self.modbus_net.connect("localhost", 1503)
    def tearDown(self):
        self.modbus_net.disconnect()
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0201_modbus_send_modbuspacket(self):
        """Test that we can send frames in BOF format."""
        frame_bof = modbus.ModbusPacket(type=modbus.MODBUS_TYPES.REQUEST)
        sent = self.modbus_net.send(frame_bof)
        self.assertEqual(sent, 7)  # replace with bytes content ?

    def test_0202_modbus_send_modbuspacket(self):
         """Test that we can send frames in Scapy format."""
         frame_scapy = ModbusADURequest()/ModbusPDU01ReadCoilsRequest()
         recv = self.modbus_net.send(frame_scapy)
         self.assertEqual(recv, 12)

    def test_0203_modbus_send_raw(self):
        """Test that we can send frames in bytes directly."""
        frame = b'\x01\xf5\x00\x00\x00\x06\x07\x06\x00\x04\x09\xc4'
        recv = self.modbus_net.sr(frame)
        self.assertEqual(bytes(recv[0]), frame)

    def test_0204_modbus_receive(self):
        """Test that received bytes are converted to ``Modbus``s."""
        frame = b'\x01\xf5\x00\x00\x00\x06\x07\x06\x00\x04\x09\xc4'
        recv = self.modbus_net.sr(frame)
        self.assertTrue(isinstance(recv[0], modbus.ModbusPacket))

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


class Test04HexToDict(unittest.TestCase):
    """Unit tests for ``HEX_TO_DICT`` (pure function, no network needed).

    ``HEX_TO_DICT(n, table)`` must return ALL n registers of the table as a
    dict numbered from 1: {1: table[0], ..., n: table[n-1]}.
    """

    def assertRegisterDict(self, result, expected_table):
        """Check that result is a dict with keys 1..n and values table[0..n-1]."""
        n = len(expected_table)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), n)
        self.assertEqual(list(result.keys()), list(range(1, n + 1)))
        for i, value in enumerate(expected_table):
            self.assertEqual(result[i + 1], value)
        self.assertEqual(result, {i + 1: v for i, v in enumerate(expected_table)})

    def test_0401_zero_registers(self):
        """HEX_TO_DICT(0, []) must return an empty dict"""
        self.assertEqual(modbus.HEX_TO_DICT(0, []), {})
        # n=0 wins even if the table holds values
        self.assertEqual(modbus.HEX_TO_DICT(0, [0x1234, 0x5678]), {})

    def test_0402_one_register(self):
        """HEX_TO_DICT(1, [v]) must return {1: v}"""
        self.assertRegisterDict(modbus.HEX_TO_DICT(1, [0xABCD]), [0xABCD])

    def test_0403_two_registers(self):
        """HEX_TO_DICT(2, [0x1234, 0x5678]) must return both registers
        (regression test: used to return only the first one)"""
        self.assertRegisterDict(modbus.HEX_TO_DICT(2, [0x1234, 0x5678]),
                                [0x1234, 0x5678])
        self.assertEqual(modbus.HEX_TO_DICT(2, [0x1234, 0x5678]),
                         {1: 4660, 2: 22136})

    def test_0404_odd_register_count(self):
        """Odd n (3) must also return all registers (old code returned n // 2)"""
        self.assertRegisterDict(modbus.HEX_TO_DICT(3, [1, 2, 3]), [1, 2, 3])

    def test_0405_n_registers(self):
        """HEX_TO_DICT(5, table) must return keys 1..5 with the 5 values"""
        table = [10, 20, 30, 40, 50]
        self.assertRegisterDict(modbus.HEX_TO_DICT(5, table), table)

    def test_0406_max_register_quantity(self):
        """Cardinality limit: MODBUS_MAX_REGISTER_QUANTITY (125) registers,
        the maximum a Modbus read response can carry, must all be returned"""
        n = modbus.MODBUS_MAX_REGISTER_QUANTITY  # 125
        table = list(range(n))
        self.assertRegisterDict(modbus.HEX_TO_DICT(n, table), table)

    def test_0407_beyond_max_register_quantity(self):
        """Just beyond the spec limit (126): HEX_TO_DICT itself imposes no
        cap, it must still return all 126 registers"""
        n = modbus.MODBUS_MAX_REGISTER_QUANTITY + 1  # 126
        table = list(range(n))
        self.assertRegisterDict(modbus.HEX_TO_DICT(n, table), table)

    def test_0408_16bit_value_boundaries(self):
        """Values at 16-bit boundaries must be preserved as-is"""
        table = [0x0000, 0xFFFF, 0x8000, 0x0001]
        result = modbus.HEX_TO_DICT(4, table)
        self.assertRegisterDict(result, table)
        self.assertEqual(result, {1: 0, 2: 65535, 3: 32768, 4: 1})

    def test_0409_table_longer_than_n(self):
        """If the table holds more entries than n, only the first n are used"""
        self.assertRegisterDict(modbus.HEX_TO_DICT(2, [1, 2, 3, 4]), [1, 2])


class _StubModbusNet:
    """Minimal ModbusNet stub: returns a canned response from sr()."""
    def __init__(self, func_code, register_values):
        self.response = SimpleNamespace(
            funcCode=func_code,
            byteCount=2 * len(register_values),  # 2 bytes per 16-bit register
            registerVal=list(register_values),
        )
    def sr(self, pkt):
        return self.response, None


class Test05ReadRegistersFunctions(unittest.TestCase):
    """Test read_holding_registers()/read_input_registers() with a stubbed
    network layer (no ncat needed): they must return ALL read registers."""

    def test_0501_read_holding_registers_returns_all(self):
        """A response with byteCount=4 (2 registers) must give 2 dict entries"""
        modnet = _StubModbusNet(modbus.FUNCTIONS.read_holding_registers,
                                [0x1234, 0x5678])
        result = modbus.read_holding_registers(modnet)
        self.assertEqual(result, {1: 4660, 2: 22136})

    def test_0502_read_input_registers_returns_all(self):
        """Same for read_input_registers()"""
        modnet = _StubModbusNet(modbus.FUNCTIONS.read_input_registers,
                                [0x1234, 0x5678])
        result = modbus.read_input_registers(modnet)
        self.assertEqual(result, {1: 4660, 2: 22136})

    def test_0503_read_holding_registers_n_registers(self):
        """5 registers (byteCount=10) must give keys 1..5 with all values"""
        table = [10, 20, 30, 40, 50]
        modnet = _StubModbusNet(modbus.FUNCTIONS.read_holding_registers, table)
        result = modbus.read_holding_registers(modnet)
        self.assertEqual(list(result.keys()), [1, 2, 3, 4, 5])
        self.assertEqual(result, {1: 10, 2: 20, 3: 30, 4: 40, 5: 50})

    def test_0504_read_holding_registers_exception_still_raises(self):
        """An exception response must still raise BOFDeviceError"""
        modnet = _StubModbusNet(modbus.FUNCTIONS.read_holding_registers_exception,
                                [])
        modnet.response.exceptCode = 0x02
        with self.assertRaises(BOFDeviceError):
            modbus.read_holding_registers(modnet)
