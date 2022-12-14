"""
ModbusPacket
------------

This class inheriting from ``BOFPacket`` is the interface between BOF's usage
of Modbus by the end user and an actual Scapy packet built using Modbus's
implementation in Scapy format.

In BOFPacket and ModbusPacket, several builtin methods and attributes are just
relayed to the Scapy Packet underneath. We also want to let the user interact
directly with the Scapy packet if she wants, using ``scapy_pkt`` attribute.

Example::

    >>> from bof.layers.modbus import *
    >>> modbus_packet = ModbusPacket(type=MODBUS_TYPES.REQUEST, function="Read Coils")
    >>> modbus_packet
    <bof.layers.modbus.modbus_packet.ModbusPacket object at 0x7f0d96f6c160>
    >>> modbus_packet.scapy_pkt
    <ModbusADURequest  |<ModbusPDU01ReadCoilsRequest  |>>

Uses Modbus specification v1.1b3 and Scapy's Modbus contrib Arthur Gervais,
Ken LE PRADO, Sebastien Mainand and Thomas Aurel.
"""

from typing import Union
from enum import Enum

import scapy.contrib.modbus as scapy_modbus
from scapy.packet import Packet

from bof import BOFPacket, to_property, BOFProgrammingError
from .modbus_constants import *


class ModbusPacket(BOFPacket):
    """Builds a ModbusPacket from a byte array or from attributes.

    :param _pkt: Modbus frame as byte array to build ModbusPacket from.
    :param scapy_pkt: Instantiated Scapy Packet to use as a ModbusPacket.
    :param type: Type of frame to build (Modbus request or response).
                 Should be a value from MODBUS_TYPES enumeration, either
                 MODBUS_TYPES.REQUEST or MODBUS_TYPES.RESPONSE.
                 A type should always be specified, except when passing scapy_pkt.
    :param function: Modbus function associated to the Modbus PDU.
                     Ignored if ``_pkt`` set. Should be a key (code as bytes or
                     int) or a value (str) from ``MODBUS_FUNCTIONS_CODES``.

    Examples of initialization::

        # "Empty" Modbus TCP request (ADU with no PDU)
        pkt = ModbusPacket(type=MODBUS_TYPES.RESPONSE)
        # Modbus Read Coil Function response frame built from a byte array
        pkt = ModbusPacket(type=MODBUS_TYPES.RESPONSE, _pkt=b'x00\x00[...]')
        # Modbus Read Coil Function request built from function code as integer
        pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST, function=0x01)
        # Modbus Read Coil Function request built from function code as bytes
        pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST, function=b'\x01')
        # Modbus Read Coil Function request built from function code name as str
        # str are taken from MODBUS_FUNCTIONS_CODES dict
        pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST, function="Read Coils")
        # Modbus Read Coil Function request built from a Scapy Packet
        modbus_frame = modbus.ModbusPacket(scapy_pkt=ModbusADURequest()/ModbusPDU01ReadCoilsRequest())
        # Field value passed directly from the constructor
        pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST, function=0x01, startAddr=0x42)
    """

    def __init__(self, _pkt: bytes = None,
                 type = None,
                 function: object = None,
                 scapy_pkt: Packet = None,
                 **kwargs) -> None:

        # set Modbus ADU based on request type
        if type == MODBUS_TYPES.RESPONSE:
            modbus_adu = scapy_modbus.ModbusADUResponse
        elif type == MODBUS_TYPES.REQUEST:
            modbus_adu = scapy_modbus.ModbusADURequest
        elif not scapy_pkt:
            raise BOFProgrammingError("Modbus requests need a type (request or response)")

        # set modbus PDU depending on initialization syntax
        # note that "not function" also catches empty str/bytes
        if _pkt or (not function and not scapy_pkt):
            self._scapy_pkt = modbus_adu(_pkt=_pkt)
        elif scapy_pkt:
            self.scapy_pkt = scapy_pkt
        elif function is not None:
            self.set_function(type, function)

        # updates fields with kwargs
        self._set_fields(**kwargs)

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def set_function(self, type: Enum, function: Union[bytes, int, str]):
        """Format packet according to the specified function (name or code)

        :param type: Type of frame to build (Modbus request or response).
                 Should be a value from MODBUS_TYPES enumeration, either
                 MODBUS_TYPES.REQUEST or MODBUS_TYPES.RESPONSE.
        :param function: Modbus function associated to the Modbus PDU.
                         Should be a key (code as bytes or int) or a value (str)
                         from ``MODBUS_FUNCTIONS_CODES``.
        """
        function_code = self._get_function_code(function)
        if type == MODBUS_TYPES.RESPONSE:
            modbus_adu = scapy_modbus.ModbusADUResponse
            if function_code == 0x0E:
                modbus_pdu = scapy_modbus._mei_types_response[function_code]
            else:
                modbus_pdu = scapy_modbus._modbus_response_classes[function_code]
        elif type == MODBUS_TYPES.REQUEST:
            modbus_adu = scapy_modbus.ModbusADURequest
            # Dirty fix: For some reason, Scapy's Modbus layer has function
            # code 0x0E for device identification, and I have 0x2B.
            if function_code in [0x0E, 0x2B]:
                modbus_pdu = scapy_modbus._mei_types_request[0x0E]
            else:
                modbus_pdu = scapy_modbus._modbus_request_classes[function_code]
        else:
            raise BOFProgrammingError(
                "Modbus requests need a type (request or response)")

        self.scapy_pkt = modbus_adu() / modbus_pdu()

    #-------------------------------------------------------------------------#
    # Private                                                                 #
    #-------------------------------------------------------------------------#

    def _get_function_code(self, function):
        """Get the code associated to ``function`` in ``MODBUS_FUNCTIONS_CODES``.
        Code is an integer, but we may need to convert it from bytes.
        :param function: Modbus function associated to the Modbus PDU.
                         Should be a key (code as bytes or int) or a value (str)
                         from ``MODBUS_FUNCTIONS_CODES``.
        """
        function_code = None
        if isinstance(function, str):
            for key, value in MODBUS_FUNCTIONS_CODES.items():
                if to_property(function) == to_property(value):
                    function_code = key
                    break
        if isinstance(function, bytes):
            function_code = int.from_bytes(function, byteorder="big")
        elif isinstance(function, int):
            function_code = function
        if (function_code not in MODBUS_FUNCTIONS_CODES.keys()):
            raise BOFProgrammingError("Invalid function ({0})".format(function))
        return function_code
