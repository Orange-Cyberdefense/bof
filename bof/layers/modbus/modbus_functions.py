"""
Modbus functions
----------------

Higher-level functions to interact with devices using Modbus TCP.

Contents:

:ModbusDevice:
    Object representation of a Modbus device with multiple properties. Only
    supports basic functions so far.
:Functions:
    High-level functions to interact with a device: read coils.

Uses Modbus specification v1.1b3 and Scapy's Modbus contrib Arthur Gervais,
Ken LE PRADO, Sebastien Mainand and Thomas Aurel.
"""

from ... import BOFDevice, BOFDeviceError
from .modbus_network import ModbusNet
from .modbus_packet import ModbusPacket
from .modbus_constants import *

###############################################################################
# MODBUS DEVICE REPRESENTATION                                                #
###############################################################################

class ModbusDevice(BOFDevice):
    pass

###############################################################################
# FUNCTIONS                                                                   #
###############################################################################

#-----------------------------------------------------------------------------#
# Discovery                                                                   #
#-----------------------------------------------------------------------------#


#-----------------------------------------------------------------------------#
# Read and write operation                                                    #
#-----------------------------------------------------------------------------#

def read_coils(modnet: ModbusNet, start_addr: int=0, quantity: int=1,
               unit_id: int=0) -> dict:
    """Read one or more Modbus coil(s) on device.

    :param modnet: Modbus connection object created previously.
    :param start_addr: First address to read coils from (default: 0).
    :param quantity: Number of coils to read from start_address (default: 1).
    :returns: A dictionary with format {coil_number: coil_value}.
    :raises BOFDeviceError: When the device responds with an exception code.

    Example::
    
        try:
            modnet = ModbusNet().connect(ip)
            coils = read_coils(modnet, quantity=10)
            for x, y in coils.items():
                print("Coil {0: 3}: {1}".format(x, y))
            modnet.disconnect()
        except BOFNetworkError as bne:
            print("ERROR:", bne, ip)
    """
    pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST, function=FUNCTIONS.read_coils,
                       startAddr=start_addr, quantity=quantity, unitId=unit_id)
    resp, _ = modnet.sr(pkt)
    if resp.funcCode == FUNCTIONS.read_coils_exception:
        print("Cannot read coils.")
        return None
    total = 1
    coils_dict = {}
    # Not a very good solution but I suck at doing this, help welcome.
    for b in range(resp.byteCount):
        coils = "{0:b}".format(resp.coilStatus[b]).ljust(8, "0")
        for coil in coils:
            coils_dict[total] = coil
            total += 1
    return coils_dict
