# BOF Discovery mpdule example
# Perform passive discovery on an industrial network by sending multicast
# packets using various protocols. Requires super user privileges.
# Usage: sudo python passive_discovery.py [network interface]
#
# passive_discovery() uses LLDP, Profinet DCP and KNX to find devices on an
# industrial devices. All packets are sent to the default multicast MAC or IP
# address of each protocol.
# LLDP is more likely used to discover switchs and network routing devices
# Profinet DCP may help us find PLC or engineering workstations from some vendors.
# KNX should give us information about KNXnet/IP gateways on the network.
#
# *********************************************************************
# *                              WARNING                              *
# *     Industrial networks and devices are critical and fragile.     *
# *   Here, we use passive discovery to avoid interacting with them   *
# *                 directly, but please remain careful.              *
# *********************************************************************

from sys import argv, path
path.append('../../')

from bof import BOFProgrammingError, DEFAULT_IFACE
from bof.modules.discovery import *

iface = argv[1] if len(argv) > 1 else DEFAULT_IFACE
try:
    devices = passive_discovery(iface=iface, verbose=True)
except BOFProgrammingError as be:
    print(be)
except OSError as oe:
    print("Invalid interface: {0}. Please specify valid network interface" \
          " as first argument.".format(iface))
