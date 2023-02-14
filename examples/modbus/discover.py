# BOF Modbus TCP example
# Read Modbus TCP devices' data.
# Usage: python discover.py DEVICE_IP_OR_RANGE [DEVICE_MODBUS_PORT]
# Example: python discover.py 192.168.1.0/24
#
# Function discover() sends a few different types of read requests to
# collect the value of data stored on Modbus devices.
# discover() returns a ModbusDevice object.
#
# discover() and ModbusDevice implemented in bof/layers/knx/knx_feature.py

from sys import argv, path
path.append('../../')
from bof import BOFProgrammingError, BOFNetworkError, IP_RANGE
from bof.layers.modbus import discover, MODBUS_PORT

if len(argv) <= 1:
    print("Usage: python {0} device_ip [modbus_port]".format(argv[0]))
    exit(-1)

try:
    ip_addrs = IP_RANGE(argv[1])
    port = MODBUS_PORT if len(argv) < 3 else argv[2]
except BOFProgrammingError as bpe:
    print("ERROR:", bpe)
    exit(-1)

for ip in ip_addrs:
    try:
        print(discover(ip))
    except BOFNetworkError:
        pass # Device did not respond
