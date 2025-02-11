"""
Modbus device
-------------

Object representation of a Modbus device.

Uses Modbus specification v1.1b3 and Scapy's Modbus contrib by Arthur Gervais,
Ken LE PRADO, Sebastien Mainand and Thomas Aurel.
"""

from ... import BOFDevice

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
        return "{0}\n\tDescription: {1}\n\tCoils ON: {2}\n\t" \
            "Discrete inputs ON: {3}\n\tHolding registers != 0: {4}\n\t" \
            "Input registers != 0: {5}".format(
                super().__str__(), self.description,
                list(self.coils_on.keys()),
                list(self.discrete_inputs_on.keys()), 
                self.holding_registers_nonzero,
                self.input_registers_nonzero, 
        )
