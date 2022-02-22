# BOF KNX example
# Send commands to KNX group addresses via KNXnet/IP server.
# Usage: python group_write.py IP KNX_GROUP_ADDR VALUE
# Example: python group_write.py 192.168.1.242 1/1/1 1
#
# Function group_write() writes a value to a KNX group address by
# setting a tunneling connection through the KNXnet/IP server.
# Returns nothing, but a value on a KNX bus has changed.
#
# group_write() implemented in bof/layers/knx/knx_feature.py
#
# *********************************************************************
# *                              WARNING                              *
# *           Changing values can have very bad side effects          *
# *                 (possibly endangering human lives)                *
# *                                                                   *
# * Please do not use this script on devices and bus when you are not *
# * absolutely sure what will happen (and preferably, use it on your  *
# * own devices...)                                                   *
# *********************************************************************

from sys import argv, path
path.append('../../')
from bof.layers.knx import *

if len(argv) != 4:
    print("Usage: python {0} device_ip knx_group_addr value".format(argv[0]))
    exit(-1)
    
group_write(argv[1], argv[2], argv[3])
