"""
Module: Discovery
-----------------

Functions for passive and active discovery of industrial devices on a network.
"""

from os import geteuid
from scapy.layers.l2 import Ether, srp
from scapy.packet import Packet
# Internal
from .. import BOFProgrammingError
from ..layers.knx import MULTICAST_ADDR as KNX_MULTICAST_ADDR, KNX_PORT, \
    search as knx_search

########################################################
# LLDP-related code will be moved to dedicated layer.  #
# Todo when completed and fully tested.                #
# Unit tests to write after moving LLDP.               #
########################################################

# LLDP -----------------------------------------------------------------------#

from scapy.contrib.lldp import *

LLDP_MULTICAST_MAC = "01:80:c2:00:00:0e"
DEFAULT_LLDP_PARAM = {
    "chassis_id": "BOF",
    "port_id": "port-BOF",
    "ttl": 20,
    "port_desc": "BOF discovery",
    "system_name": "BOF",
    "system_desc": "BOF discovery"
    }

class LLDPDevice(object):
    """Object representation of a device responding to LLDP requests."""
    raw_pkt: Packet = None
    mac_addr: str = None
    chassis_id: str = None
    port_id: str = None
    port_desc: str = None
    system_name: str = None
    system_desc: str = None
    capabilities: dict = None
    ip_addr: str = None
    
    def __init__(self, pkt: Packet=None):
        if pkt:
            self.parse(pkt)

    def parse(self, pkt: Packet=None) -> None:
        """Parse LLDP response to store device information.

        :param pkt: LLDP packet, including Ethernet (Ether) layer.

        Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
        """
        # Not tested yet
        self.raw_pkt = pkt
        self.mac_addr = pkt["Ether"].src
        self.chassis_id = pkt["LLDPDUChassisID"].id
        self.port_id = pkt["LLDPDUPortID"].id
        self.port_desc = pkt["LLDPDUPortDescription"].description
        self.system_name = pkt["LLDPDUSystemName"].system_name
        self.system_desc = pkt["LLDPDUSystemDescription"].description
        self.capabilities = pkt["LLDPDUSystemCapabilities"] # TODO
        self.ip_addr = pkt["LLDPDUManagementAddress"].management_address # TODO: subtypes
        # IP address as a property so that we can return it only if subtype==IPv4
        # TODO: Profibus stuff (e.g. for Siemens devices)

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
        /lldp_ttl/lldp_portdesc/lldp_sysname/lldp_sysdesc/lldp_capab \
        /lldp_mgmt/lldp_end

def get_lldp_info(pkt: Packet) -> LLDPDevice:
    """Parses a LLDP packet to extract information on source device.

    :param pkt: Received packet as a Scapy Packet object.

    Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
    """
    # Should LLDP be detected directly when receiving a packet with srp?
    # Seen as Raw when created from bytes directly.
    pkt.show2()
    return LLDPDevice(pkt)

def lldp_request(mac_addr: str=LLDP_MULTICAST_MAC, mgmt_ip: str="0.0.0.0",
                 lldp_param: dict=None) -> list:
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
    replies, norep = srp(packet, multi=1, iface="eth0", timeout=1, verbose=False)
    devices = []
    for reply in replies:
        devices.append(get_lldp_info(reply))
    return devices    

# End of LLDP ----------------------------------------------------------------#

###############################################################################
# LLDP                                                                        #
###############################################################################

def lldp_discovery(mac_addr: str=LLDP_MULTICAST_MAC, mgmt_ip: str="0.0.0.0",
                   lldp_param: dict=None) -> list:
    """Search for devices on an network using multicast LLDP requests.

    Implementation in LLDP layer.
    """
    return lldp_request(mac_addr, mgmt_ip, lldp_param)
    
###############################################################################
# KNX                                                                         #
###############################################################################

def knx_discovery(ip: str=KNX_MULTICAST_ADDR, port=KNX_PORT):
    """Search for KNX devices on an network using multicast.

    Implementation in KNX layer.
    """
    return knx_search(ip, port)

###############################################################################
# GLOBAL                                                                      #
###############################################################################

def passive_discovery(knx_multicast: str=KNX_MULTICAST_ADDR, knx_port=KNX_PORT,
                      lldp_multicast: str=LLDP_MULTICAST_MAC,
                      verbose: bool=False):
    """Discover devices on an industrial network using passive methods.

    Requests are sent to protocols' multicast addresses or via broadcast.
    Currently, LLDP and KNX are supported.
    """
    vprint = lambda msg: print("[BOF] {0}.".format(msg)) if verbose else None
    protocols = {
        # Protocol name: [Discovery function, Multicast address]
        "LLDP": [lldp_discovery, lldp_multicast],
        "KNX": [knx_discovery, knx_multicast]
    }
    total_devices = []
    for protocol, proto_args in protocols.items():
        discovery_fct, multicast_addr = proto_args
        vprint("Sending {0} request to {1}".format(protocol, multicast_addr))
        devices = discovery_fct()
        nb = len(devices)
        vprint("{0} {1} {2} found".format(nb if nb else "No", protocol,
                                          "device" if nb < 1 else "devices"))
        total_devices += devices
    # TODO: Merge devices based on their address but still keep all their
    # attributes from different device objects.
    for device in total_devices:
        vprint(device)
    return total_devices
