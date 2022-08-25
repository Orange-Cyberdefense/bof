"""
Module: Discovery
-----------------

Functions for passive and active discovery of industrial devices on a network.
"""

from os import geteuid
from scapy.layers.l2 import Ether, srp
from scapy.packet import Packet
from scapy.contrib.lldp import *
# Internal
from .. import BOFProgrammingError

# Should this part and parsing be moved to layers? Yes probably!!! #
####################################################################

LLDP_MULTICAST_MAC = "01:80:c2:00:00:0e"
DEFAULT_LLDP_PARAM = {
    "chassis_id": "BOF",
    "port_id": "port-BOF",
    "ttl": 20,
    "port_desc": "BOF discovery",
    "system_name": "BOF",
    "system_desc": "BOF discovery"
    }

def create_lldp_packet(mac_addr: str=LLDP_MULTICAST_MAC, mgmt_ip: str="0.0.0.0",
                       lldp_param: dict=None) -> Packet:
    """Create a LLDP packet for discovery to be sent on Ethernet layer.

    :param mgmt_ip: Source IPv4 address to include as management address.
    :param lldp_param: Dictionary containing LLDP info to set. Optional.

    Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
    """
    # Dirty conversion from IP to hex, can be improved
    iphex = b''.join([int(i).to_bytes(1, byteorder="big") for i in mgmt_ip.split(".")])
    lldp_param = lldp_param if lldp_param else DEFAULT_LLDP_PARAM

    # Not all blocks may be needed, requires extended testing.
    try:
        lldp_chassisid = LLDPDUChassisID(subtype="locally assigned",
                                         id=lldp_param["chassis_id"])
        lldp_portid = LLDPDUPortID(id=lldp_param["port_id"])
        lldp_ttl = LLDPDUTimeToLive(ttl=lldp_param["ttl"])
        lldp_portdesc = LLDPDUPortDescription(description=lldp_param["port_desc"])
        lldp_sysname = LLDPDUSystemName(system_name=lldp_param["system_name"])
        lldp_sysdesc = LLDPDUSystemDescription(description=lldp_param["system_desc"])
        lldp_mgmt = LLDPDUManagementAddress(management_address_subtype="IPv4",
                                            management_address=iphex,
                                            interface_numbering_subtype="ifIndex",
                                            interface_number=1)
        lldp_capab = LLDPDUSystemCapabilities()
        lldp_end = LLDPDUEndOfLLDPDU()
    except KeyError as ke: # Occus if an entry is missing in lldp_param
        raise BOFProgrammingError("Invalid parameter for LLDP: {0}".format(ke)) from None

    return Ether(dst=mac_addr)/LLDPDU()/lldp_chassisid/lldp_portid \
        /lldp_ttl/lldp_portdesc/lldp_sysname/lldp_sysdesc/lldp_capab/lldp_mgmt/lldp_end
    
###############################################################################
# LLDP                                                                        #
###############################################################################

def lldp_discovery(mac_addr: str=LLDP_MULTICAST_MAC, mgmt_ip: str="0.0.0.0",
                   lldp_param: dict=None) -> dict:
    """Send LLDP (Link Layer Discovery Protocol) packets on Ethernet layer.

    Some industrial devices and switches respond to them.
    Multicast is used by default.
    Requires super-user privileges to send on Ethernet link.

    :param mac_addr: MAC address to send the LLDP packet to (default: multicast)
    :param mgmt_ip: Source IPv4 address to include as management address.
    :param lldp_param: Dictionary containing LLDP info to set. Optional.

    Example::

      from bof.modules.discovery import *

      devices = lldp_discovery()
      for device in devices:
        print(device)

    Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
    """
    packet = create_lldp_packet(mac_addr, mgmt_ip, lldp_param)
    # Using Scapy's send function on Ethernet, requires super user privilege
    if geteuid() != 0:
        raise BOFProgrammingError("Super user privileges required to send LLDP requests")
    rep, norep = srp(packet, multi=1, iface="eth0", timeout=1, verbose=False)
    # Debug
    for reply in rep:
        print(rep)
