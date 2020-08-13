"""unittest for opcua network communication, implementing ``bof.network``'s 
``TCP`` class.
"""

import unittest
from bof import opcua, byte, BOFLibraryError, BOFProgrammingError

OPCUA_SERVER = ("127.0.0.1", 4840)
OPCUA_ENDPOINT = "opc.tcp://localhost:4840"

#@unittest.skip("Need an OPC UA server running")
class Test01OpcuaNetConnect(unittest.TestCase):        
    def test_open_connection(self):
        opcuanet = opcua.OpcuaNet()
        opcuanet.tcp_connect(*OPCUA_SERVER)
        response = opcuanet._open_connection(OPCUA_SERVER, OPCUA_ENDPOINT)
        expected_attributes = ['message_type', 'is_final', 'message_size',
                               'protocol_version', 'receive_buffer_size', 
                               'send_buffer_size', 'max_message_size', 
                               'max_chunk_count']
        self.assertEqual(response.attributes, expected_attributes)