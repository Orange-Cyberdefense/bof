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

from ... import BOFDevice, BOFDeviceError, IS_IP
from .modbus_network import ModbusNet
from .modbus_packet import ModbusPacket
from .modbus_constants import *

def HEX_TO_BIN_DICT(byte_count, hex_table):
    """Convert hex value table on one or more bytes to binary bit in a dict.

    Example:
    Hex value 0x15 on 2 bytes will be translated to 10101000 00000000
    This binary will be stored in a numbered dict starting from 1: {
      1: 1,
      2: 0,
      3: 1,
      ...
    }
    """
    index = 1
    bin_dict = {}
    # Not a very good solution but I suck at doing this, help welcome.
    for b in range(byte_count):
        # Convert, reverse (to keep trailing 0 at front), padding after
        values = "{0:b}".format(hex_table[b])[::-1].ljust(8, "0")
        for value in values:
            bin_dict[index] = int(value)
            index += 1
    return bin_dict

def HEX_TO_DICT(byte_count, hex_table):
    """Convert hex value table on one or more bytes to binary bit in a dict.

    Example:
    Hex value 0x15 on 2 bytes will be translated to 10101000 00000000
    This binary will be stored in a numbered dict starting from 1: {
      1: 1,
      2: 0,
      3: 1,
      ...
    }
    """
    index = 1
    hex_dict = {}
    for b in range(byte_count // 2):
        hex_dict[index] = hex_table[b]
        index += 1
    return hex_dict

###############################################################################
# MODBUS DEVICE REPRESENTATION                                                #
###############################################################################

class ModbusDevice(BOFDevice):
    protocol: str = "Modbus TCP"
    name: str = ""
    coils: dict = None
    discrete_inputs: dict = None
    holding_registers: dict = None
    input_registers: dict = None

    @property
    def coils_on(self):
        return {x:y for x,y in self.coils.items() if y}

    @property
    def discrete_inputs_on(self):
        return {x:y for x,y in self.discrete_inputs.items() if y}

    @property
    def holding_registers_nonzero(self):
        return {x:y for x,y in self.holding_registers.items() if y}

    @property
    def input_registers_nonzero(self):
        return {x:y for x,y in self.input_registers.items() if y}
    
    def __str__(self):
        return "{0}\n\tCoils ON: {1}\n\tDiscrete inputs ON: {2}\n\t" \
            "Holding registers != 0: {3}\n\tInput registers != 0: {4}".format(
                super().__str__(), list(self.coils_on.keys()),
                list(self.discrete_inputs_on.keys()), 
                self.holding_registers_nonzero,
                self.input_registers_nonzero, 
        )
    
###############################################################################
# FUNCTIONS                                                                   #
###############################################################################

#-----------------------------------------------------------------------------#
# Discovery                                                                   #
#-----------------------------------------------------------------------------#

def discover(ip: str, port: int=MODBUS_PORT) -> ModbusDevice:
    """Returns discovered information about a device.
    So far, we only read the different types of data stored on a device.

    :param ip_range: IPv4 address of a Modbus device.
    :param port: Modbus TCP port, default is 502.
    :returns: A ModbusDevice object.
    :raises BOFProgrammingError: if IP is invalid.
    :raises BOFNetworkError: if device cannot be reached.
    :raises BOFDeviceError: if request is not supported on remote device.
    """
    IS_IP(ip)
    device = ModbusDevice()
    modnet = ModbusNet().connect(ip)
    try:
        device.coils = read_coils(modnet, quantity=MODBUS_MAX_COIL_QUANTITY)
    except BOFDeviceError as bde:
        device.coils = {0: bde}
    try:
        device.discrete_inputs = read_discrete_inputs(
            modnet,quantity=MODBUS_MAX_DISCRETE_QUANTITY)
    except BOFDeviceError as bde:
        device.discrete_inputs = {0: bde}
    try:
        device.holding_registers = read_holding_registers(
            modnet, quantity=MODBUS_MAX_REGISTER_QUANTITY)
    except BOFDeviceError as bde:
        device.holding_registers = {0: bde}
    try:
        device.input_registers = read_input_registers(
            modnet, quantity=MODBUS_MAX_REGISTER_QUANTITY)
    except BOFDeviceError as bde:
        device.input_registers = {0: bde}
    modnet.disconnect()
    return device

#-----------------------------------------------------------------------------#
# Read and write operation                                                    #
#-----------------------------------------------------------------------------#

def read_coils(modnet: ModbusNet, start_addr: int=0, quantity: int=1,
               unit_id: int=0) -> dict:
    """Read one or more Modbus coil(s) on device.

    :param modnet: Modbus connection object created previously.
    :param start_addr: First address to read coils from (default: 0).
    :param quantity: Number of coils to read from start_address (default: 1).
    :returns: A dictionary with format {coil_number: value}.
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
        raise BOFDeviceError("Cannot read coils.")
    return HEX_TO_BIN_DICT(resp.byteCount, resp.coilStatus)

def read_discrete_inputs(modnet: ModbusNet, start_addr: int=0, quantity: int=1,
                  unit_id: int=0) -> dict:
    """Read one or more Modbus discrete input(s) on device.

    :param modnet: Modbus connection object created previously.
    :param start_addr: First address to read inputs from (default: 0).
    :param quantity: Number of inputs to read from start_address (default: 1).
    :returns: A dictionary with format {input_number: value}.
    :raises BOFDeviceError: When the device responds with an exception code.

    Example: See ``read_coils()``
    """
    pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST,
                       function=FUNCTIONS.read_discrete_inputs,
                       startAddr=start_addr, quantity=quantity, unitId=unit_id)
    resp, _ = modnet.sr(pkt)
    if resp.funcCode == FUNCTIONS.read_discrete_inputs_exception:
        raise BOFDeviceError("Cannot read discrete inputs.")
    return HEX_TO_BIN_DICT(resp.byteCount, resp.inputStatus)

def read_holding_registers(modnet: ModbusNet, start_addr: int=0, quantity: int=1,
                  unit_id: int=0) -> dict:
    """Read one or more Modbus holding register(s) on device.

    :param modnet: Modbus connection object created previously.
    :param start_addr: First address to read registers from (default: 0).
    :param quantity: Number of registers to read from start_address (default: 1).
    :returns: A dictionary with format {reg_number: value}.
    :raises BOFDeviceError: When the device responds with an exception code.

    Example: See ``read_coils()``
    """
    pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST,
                       function=FUNCTIONS.read_holding_registers,
                       startAddr=start_addr, quantity=quantity, unitId=unit_id)
    resp, _ = modnet.sr(pkt)
    if resp.funcCode == FUNCTIONS.read_holding_registers_exception:
        raise BOFDeviceError("Cannot read holding registers.")

    return HEX_TO_DICT(resp.byteCount // 2, resp.registerVal)

def read_input_registers(modnet: ModbusNet, start_addr: int=0, quantity: int=1,
                  unit_id: int=0) -> dict:
    """Read one or more Modbus input register(s) on device.

    :param modnet: Modbus connection object created previously.
    :param start_addr: First address to read registers from (default: 0).
    :param quantity: Number of registers to read from start_address (default: 1).
    :returns: A dictionary with format {reg_number: value}.
    :raises BOFDeviceError: When the device responds with an exception code.

    Example: See ``read_coils()``
    """
    pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST,
                       function=FUNCTIONS.read_input_registers,
                       startAddr=start_addr, quantity=quantity, unitId=unit_id)
    resp, _ = modnet.sr(pkt)
    if resp.funcCode == FUNCTIONS.read_input_registers_exception:
        raise BOFDeviceError("Cannot read input registers.")

    return HEX_TO_DICT(resp.byteCount // 2, resp.registerVal)
