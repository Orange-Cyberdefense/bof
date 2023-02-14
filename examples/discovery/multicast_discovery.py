# BOF Discovery mpdule example
# Perform discovery using multicast on an industrial network using
# various protocols. Requires super user privileges.
# Usage: sudo python multicast_discovery.py [network interface]
#
# multicast_discovery() uses LLDP, Profinet DCP and KNX to find devices on an
# industrial network. All packets are sent to the default multicast MAC or IP
# address of each protocol.
# LLDP is more likely used to discover switchs and network routing devices
# Profinet DCP may help us find PLC or engineering workstations from some vendors.
# KNX should give us information about KNXnet/IP gateways on the network.
#
# *********************************************************************
# *                              WARNING                              *
# *     Industrial networks and devices are critical and fragile.     *
# *   Here, we use multicast discovery to only reach devices that     *
# *   suscribed to specific multicast addresses (and therefore not    *
# *       send requests to devices that may not support them,         *
# *                      but please remain careful.                   *
# *********************************************************************

from sys import argv, path
path.append('../../')

from bof import BOFProgrammingError, DEFAULT_IFACE
from bof.modules.discovery import *

iface = argv[1] if len(argv) > 1 else DEFAULT_IFACE
try:
    devices = multicast_discovery(iface=iface, verbose=True)
except BOFProgrammingError as be:
    print(be)
except OSError as oe:
    print("Network error: {0}".format(oe))
