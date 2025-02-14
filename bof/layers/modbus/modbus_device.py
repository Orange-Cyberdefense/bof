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
