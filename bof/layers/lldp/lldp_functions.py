"""
LLDP functions
--------------

Higher-level functions for network discovery using LLDP.

Contents:

:LLDPDevice:
    Object representation of a device discovered via LLDP.
:Listen:
    Sync and async functions to listen on the network for LLDP multicast
    requests.
:Send:
    Create basic LLDP requests and send them via multicast.

Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
"""

from os import geteuid
from ipaddress import IPv4Address, AddressValueError

from scapy.packet import Packet
from scapy.layers.l2 import Ether
from scapy.sendrecv import AsyncSniffer, sendp
from scapy.contrib.lldp import *

from ... import BOFProgrammingError, BOFDevice, DEFAULT_IFACE
from .lldp_constants import *

#-----------------------------------------------------------------------------#
# LLDP device                                                                 #
#-----------------------------------------------------------------------------#

class LLDPDevice(BOFDevice):
    """Object representation of a device described LLDP requests."""
    protocol:str = "LLDP"
    name: str = None # system_name
    description: str = None # system_desc
    mac_address: str = None
    ip_address: str = None
    # LLDP specific
    chassis_id: str = None
    port_id: str = None
    port_desc: str = None
    capabilities: dict = None
    
    def __init__(self, pkt: Packet=None):
        if pkt:
            self.parse(pkt)

    def parse(self, pkt: Packet=None) -> None:
        """Parse LLDP response to store device information.

        :param pkt: LLDP packet (Scapy), including Ethernet (Ether) layer.
        """
        self.name = pkt["LLDPDUSystemName"].system_name.decode('utf-8')
        self.description = pkt["LLDPDUSystemDescription"].description.decode('utf-8')
        if "Ether" in pkt:
            self.mac_address = pkt["Ether"].src
        try: # TODO: Subtypes, we only handle IPv4 so far...
            self.ip_address = IPv4Address(pkt["LLDPDUManagementAddress"].management_address)
            # IP address as a property so that we can return it only if subtype==IPv4
        except AddressValueError as ave:
            raise BOFProgrammingError("Subtypes other than IPv4 not implemented yet.")
        self.chassis_id = pkt["LLDPDUChassisID"].id
        if not isinstance(self.chassis_id, str):
            self.chassis_id = self.chassis_id.decode('utf-8')
        self.port_id = pkt["LLDPDUPortID"].id.decode('utf-8')
        self.port_desc = pkt["LLDPDUPortDescription"].description.decode('utf-8')
        self.capabilities = pkt["LLDPDUSystemCapabilities"] # TODO

#-----------------------------------------------------------------------------#
# Listen to LLDP packets on the network                                       #
#-----------------------------------------------------------------------------#

def start_listening(iface: str=DEFAULT_IFACE,
                      timeout: int=DEFAULT_TIMEOUT) -> AsyncSniffer:
    """Listen for LLDP requests sent on the network, usually via multicast.

    We don't need to send a request for the others to replies, however we need
    to wait for devices to talk, so timeout should be high (at least 10s).
    Requires super-user privileges to receive on Ethernet link.

    :param iface: Network interface to use to send the packet.
    :param timeout: Sniffing time. We have to wait for LLPD spontaneous multcast.
    """
    if geteuid() != 0:
        raise BOFProgrammingError("Super user privileges required to receive LLDP packets")
    sniffer = AsyncSniffer(iface=iface, count=1, #DEBUG: prn=lambda x: x.summary(),
                           lfilter=lambda x: LLDPDU in x, store=True)
    sniffer.start()
    return sniffer

def stop_listening(sniffer: AsyncSniffer) -> list:
    if sniffer.running:
        sniffer.stop()
    return sniffer.results

def listen_sync(iface: str=DEFAULT_IFACE, timeout: int=DEFAULT_TIMEOUT) -> list:
    """Search for devices on an network by listening to LLDP requests.
    
    Converts back asynchronous to synchronous with sleep (silly I know).  If you
    want to keep asynchrone, call directly ``start_listening`` and
    ``stop_listening`` in your code.
    """
    sniffer = start_listening(iface, timeout)
    sleep(timeout)
    results = stop_listening(sniffer)
    devices = []
    for result in results:
        devices.append(LLDPDevice(result))
    return devices

#-----------------------------------------------------------------------------#
# Send LLDP packets on the network                                            #
#-----------------------------------------------------------------------------#

def create_packet(lldp_param: dict=DEFAULT_PARAM) -> Packet:
    """Create a LLDP packet for discovery to be sent on Ethernet layer.

    :param lldp_param: Dictionary containing LLDP info to set. Optional.
    """
    try:
        # Dirty conversion from IP to hex, can be improved
        mgmt_ip = lldp_param["management_address"]
        iphex = b''.join([int(i).to_bytes(1, byteorder="big") for i in mgmt_ip.split(".")])
        # Not all blocks may be needed, requires extended testing.
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
    except KeyError as ke: # Occurs if an entry is missing in lldp_param
        raise BOFProgrammingError("Invalid parameter for LLDP: {0}".format(ke)) from None
    return LLDPDU()/lldp_chassisid/lldp_portid \
        /lldp_ttl/lldp_portdesc/lldp_sysname/lldp_sysdesc/lldp_capab \
        /lldp_mgmt/lldp_end

def send_multicast(pkt: Packet=None, iface: str=DEFAULT_IFACE, mac_addr:
                   str=MULTICAST_MAC) -> Packet:
    """Send a LLDP (Link Layer Discovery Protocol) packet on Ethernet layer.

    Multicast is used by default.
    Requires super-user privileges to send on Ethernet link.

    :param pkt: LLDP Scapy packet. If not specified, creates a default one.
    :param iface: Network interface to use to send the packet.
    :param mac_addr: MAC address to send the LLDP packet to (default: multicast)
    :returns: The packet that was sent, mostly for debug and testing purposes.
    """
    if not pkt:
        pkt = create_packet()
    if "Ether" not in pkt:
        pkt = Ether(type=0x88cc, dst=mac_addr)/pkt
    # Using Scapy's send function on Ethernet, requires super user privilege
    if geteuid() != 0:
        raise BOFProgrammingError("Super user privileges required to send LLDP requests")
    # Timeout should be high because devices take time to respond
    sendp(packet, multi=1, iface=iface, verbose=False)
    return pkt
