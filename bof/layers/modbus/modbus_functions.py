"""
Modbus functions
----------------

Higher-level functions to interact with devices using Modbus TCP.

Contents:

:ModbusDevice:
    Object representation of a Modbus device with multiple properties. Only
    supports basic functions so far.
:Functions:
    High-level functions to interact with a device.

Uses Modbus specification v1.1b3 and Scapy's Modbus contrib by Arthur Gervais,
Ken LE PRADO, Sebastien Mainand and Thomas Aurel.
"""

from ... import BOFDevice, BOFDeviceError, BOFNetworkError, IS_IP, log
from .modbus_network import ModbusNet
from .modbus_packet import ModbusPacket
from .modbus_constants import *

def HEX_TO_BIN_DICT(byte_count, hex_table):
    """Convert hex value table on one or more bytes to binary bit in a dict.

    Example:
    Hex value 0x15 on 2 bytes will be translated to 10101000 00000000
    This binary will be stored in a numbered dict starting from 1:
    { 1: 1, 2: 0, 3: 1, ... }
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
    This binary will be stored in a numbered dict starting from 1:
    { 1: 1, 2: 0, 3: 1, ... }
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
    name: str = "" # ProductCode
    description: dict = None
    coils: dict = None
    discrete_inputs: dict = None
    holding_registers: dict = None
    input_registers: dict = None

    def __init__(self):
        self.description = {}
    
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
        full_read_device_identification(modnet, device)
    except BOFDeviceError as bde:
        log("Modbus: Function code 43 (Read Device Id) not supported")
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
        msg = MODBUS_EXCEPTIONS[resp.exceptCode]
        raise BOFDeviceError("Cannot read coils (Exception returned: {0}).".format(msg))
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
        msg = MODBUS_EXCEPTIONS[resp.exceptCode]
        raise BOFDeviceError("Cannot read discrete inputs (Exception returned: {0}).".format(msg))
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
        msg = MODBUS_EXCEPTIONS[resp.exceptCode]
        raise BOFDeviceError("Cannot read holding registers (Exception returned: {0}).".format(msg))

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
        msg = MODBUS_EXCEPTIONS[resp.exceptCode]
        raise BOFDeviceError("Cannot read input registers (Exception returned: {0}).".format(msg))

    return HEX_TO_DICT(resp.byteCount // 2, resp.registerVal)

def read_device_identification(modnet: ModbusNet, read_code: int=1,
                               object_id: int=0x00):
    """Read device information (if the devices supports function code 43).

    :param modnet: Modbus connection object created previously.
    :param readCode: Read level to use: 1:basic, 2:regular, 3:extended, 4:specific.
    :param objectId: Object to read: 0: VendorName, 1:ProductCode, 2:Revision,
                     3: VendorUrl, 4: ProductName, 5: ModelName, 6: UserAppName.
    :returns: A tuple (objectId, value) from the response.
    :raises BOFDeviceError: When the device does not respond or responds
                            with an exception code.
    """
    pkt = ModbusPacket(type=MODBUS_TYPES.REQUEST,
                       function=FUNCTIONS.read_device_identification,
                       readCode=read_code, objectId=object_id)
    try:
        resp, _ = modnet.sr(pkt)
    except BOFNetworkError as bne: # Modnet object exist: connection should be ok
        raise BOFDeviceError("Cannot read device identification.") from None
    if resp.funcCode == FUNCTIONS.read_device_identification_exception:
        msg = MODBUS_EXCEPTIONS[resp.exceptCode]
        raise BOFDeviceError("Cannot read device identification (Exception returned: {0}).".format(msg))
    return resp.id, resp.value
    
def full_read_device_identification(modnet: ModbusNet, device: ModbusDevice=None):
    """Read all information available on the device using read device id requests.

    This function sends as many read device identification requests as there are
    objects to read (6). Returns data as a ModbusDevice object.

    :param modnet: Modbus connection object created previously.
    :param device: ModbusDevice object. If none: creates a new one.
    :returns: The ModbusDevice object.
    :raises BOFDeviceError: When the device responds with an exception code.
    """
    if device == None:
        device = ModbusDevice()
    read_code = 3 # Extended
    for object_id, name in MODBUS_OBJECT_ID.items():
        key, value = read_device_identification(modnet, read_code, object_id)
        # Store to device object
        if key == 0x01: # ProductCode
            device.name = value.decode('utf-8')
        key = MODBUS_OBJECT_ID[key]
        device.description[key] = value.decode('utf-8')
    return device
