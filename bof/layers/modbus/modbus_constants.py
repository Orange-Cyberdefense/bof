"""
Modbus TCP constants
--------------------

Protocol-dependent constants (network and functions) for Modbus TCP.
"""

from ... import to_property
from enum import Enum

MODBUS_TYPES = Enum('MODBUS_TYPES', 'REQUEST RESPONSE')

# User defined function codes from 65 to 72, and from 100 to 110 (decimal)

MODBUS_FUNCTIONS_CODES = FUNCTION_CODES = {
    0x01: "Read Coils",
    0x02: "Read Discrete Inputs",
    0x03: "Read Holding Registers",
    0x04: "Read Input Registers",
    0x05: "Write Single Coil",
    0x06: "Write Single Register",
    0x07: "Read ExceptionStatus",
    0x08: "Diagnostics",
    0x0B: "Get Comm Event Counter",
    0x0C: "Get Comm Event Log",
    0x0E: "Read Device Identification",
    0x0F: "Write Multiple Coils",
    0x10: "Write Multiple Registers",
    0x11: "Report Slave Id",
    0x14: "Read File Record",
    0x15: "Write File Record",
    0x16: "Mask Write Register",
    0x17: "Read Write Multiple Registers",
    0x18: "Read FIFO Queue",
    0x2B: "Read device identification", # Subcode 14
    # Exception codes for functions (== Function code + 0x80)
    0x81: "Read Coils Exception",
    0x82: "Read Discrete Inputs Exception",
    0x83: "Read Holding Registers Exception",
    0x84: "Read Input Registers Exception",
    0x85: "Write Single Coil Exception",
    0x86: "Write Single Register Exception",
    0x87: "Read Exception Status Exception",
    0x88: "Diagnostics Exception",
    0x8B: "Get Comm Event Counter Exception",
    0x8C: "Get Comm Event Log Exception",
    0x8F: "Write Multiple Coils Exception",
    0x90: "Write Multiple Registers Exception",
    0x91: "Report Slave Id Exception",
    0x94: "Read File Record Exception",
    0x95: "Write File Record Exception",
    0x96: "Mask Write Register Exception",
    0x97: "Read Write Multiple Exception",
    0x98: "Read FIFO Queue Exception"
}

FUNCTIONS = type('FUNCTIONS', (object,),
           {to_property(v):k \
            for k,v in MODBUS_FUNCTIONS_CODES.items()})()

MODBUS_EXCEPTION_OFFSET = EXCEPTION_OFFSET = 0x80
