# BOF KNX example
# Request a KNXnet/IP gateway to describe itself.
# Usage: python discover.py DEVICE_IP [DEVICE_KNX_PORT]
# Example: python discover.py 192.168.1.242
#
# Function discover() sends a DESCRPTION REQUEST (KNXnet/IP) to a
# KNXnet/IP device IPv4 address on the KNXnet/IP port (default is 3671,
# custom port can be used as a second argument).
# discover() returns a KNXDevice object.
#
# discover() and KNXDevice implemented in bof/layers/knx/knx_feature.py

from sys import argv, path
path.append('../../')
from bof.layers.knx import discover

if len(argv) == 2:
    description = discover(argv[1])
elif len(argv) == 3:
    description = discover(argv[1], argv[2])
else:
    print("Usage: python {0} device_ip [knx_port]".format(argv[0]))
    exit(-1)

print(description)
