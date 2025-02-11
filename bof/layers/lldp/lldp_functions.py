"""
LLDP functions
--------------

Higher-level functions for network discovery using LLDP.

Contents:

:Listen:
    Sync and async functions to listen on the network for LLDP multicast
    requests.
:Send:
    Create basic LLDP requests and send them via multicast.

Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
"""

from os import geteuid
from time import sleep

# Scapy
from scapy.packet import Packet
from scapy.layers.l2 import Ether
from scapy.sendrecv import AsyncSniffer, sendp
from scapy.contrib.lldp import *

# Internal
from ... import BOFProgrammingError, DEFAULT_IFACE
from .lldp_device import LLDPDevice
from .lldp_constants import DEFAULT_TIMEOUT, DEFAULT_PARAM, MULTICAST_MAC
            
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
