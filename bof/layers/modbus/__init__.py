"""
Modbus TCP
----------

BOF's ``modbus`` submodule can be imported with::

    from bof.layers import modbus
    from bof.layers.modbus import *

The following files are available in the module:

:modbus_network:
    Class for network communication with Modbus over TCP. Inherits from BOF's
    ``network`` ``TCP`` class. Implements methods to connect, disconnect and
    mostly send and receive frames as ``ModbusPacket`` objects.

:modbus_packet:
    Object representation of a Modbus packet. ``ModbusPacket`` inherits
    ``BOFPacket`` and uses Uses Modbus specification v1.1b3 and Scapy's Modbus
    contrib Arthur Gervais, Ken LE PRADO, Sebastien Mainand and Thomas Aurel.

:modbus_functions:
    Higher-level functions to discover and interact with devices via Modbus TCP.
"""

from .modbus_network import *
from .modbus_packet import *
from .modbus_functions import *
