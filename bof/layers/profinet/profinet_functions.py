"""
Profinet DCP functions
----------------------

Higher-level functions for network discovery using PNDCP.

Send and receive identify requests and response to discover devices.

Uses Scapy's Profinet IO contrib by Gauthier Sebaux and Profinet DCP contrib
by Stefan Mehner (stefan.mehner@b-tu.de).
"""

from os import geteuid
from time import sleep
from packaging.version import parse as version_parse

# Scapy
from scapy import VERSION as scapy_version
from scapy.packet import Packet
from scapy.layers.l2 import Ether, sendp
from scapy.sendrecv import AsyncSniffer
if version_parse(scapy_version) <= version_parse("2.4.5"):
    # Layer pnio_dcp raises deprecation warnings for Scapy < 2.5.0
    from warnings import filterwarnings
    from cryptography.utils import CryptographyDeprecationWarning
    filterwarnings('ignore', category=SyntaxWarning)
    filterwarnings('ignore', category=CryptographyDeprecationWarning)
from scapy.contrib.pnio import ProfinetIO
from scapy.contrib.pnio_dcp import *

# Internal
from ... import BOFProgrammingError, DEFAULT_IFACE, to_property
from .profinet_constants import *
from .profinet_device import ProfinetDevice


#-----------------------------------------------------------------------------#
# Send PNDCP identify packets on the network                                 #
#-----------------------------------------------------------------------------#

def create_identify_packet() -> Packet: # Should become generic at some point.
    """Create a Profinet DCP packet for discovery to be sent on Ethernet layer."""
    pn_io = ProfinetIO(frameID=DCP_IDENTIFY_REQUEST_FRAME_ID)
    pn_dcp = ProfinetDCP(service_id="Identify", service_type=DCP_REQUEST,
                         xid=0x1366b490, # Can't figure out why, or even what is xid...
                         reserved=192, # Reserved is actually ResponseDelay here
                         option=255, sub_option=255, dcp_data_length=4)
    pkt = pn_io/pn_dcp
    return pkt

def send_identify_request(iface: str=DEFAULT_IFACE,
                          mac_addr: str=MULTICAST_MAC,
                          timeout: int=DEFAULT_TIMEOUT) -> list:
    """Send PN-DCP (Profinet Discovery/Config Proto) packets on Ethernet layer.

    Some industrial devices such as PLCs respond to them.
    Responses may be embedded in 802.1Q frames.
    Multicast is used by default.
    Requires super-user privileges to send on Ethernet link.

    :param iface: Network interface to use to send the packet.
    :param mac_addr: MAC address to send the PN-DCP packet to (default: multicast)
    :param timeout: Timeout for responses. More than 10s because some devices
                    take time to respond.
    """
    packet = Ether(type=ETHER_TYPE_PROFINET, dst=mac_addr)/create_identify_packet()
    # Using Scapy's send function on Ethernet, requires super user privilege
    if geteuid() != 0:
        raise BOFProgrammingError("Super user privileges required to send PN-DCP requests")

    # Profinet DCP responses are sometimes encapsulated inside 802.1Q, sometimes not
    # Here are some additional restrictive filters, they may prevent some replies
    # from being intercepted but they may be required sometimes until someone comes
    # up with a universal filter
    # x["Ether"].type == ETHER_TYPE_VLAN \
    #(x["Dot1Q"].type == ETHER_TYPE_PROFINET and "ProfinetDCP" in x)
    # Exclude "Padding" prevents from having an additional "None" result
    # Please create an issue if it prevents from discovering some devices
    lfilter = lambda x: "Ether" in x and "ProfinetDCP" in x and not "Padding" in x
    # We have to set a listener and not use srp in case the request is encapsulated
    # (Scapy does not detect it as a reply in this case). So we sniff the network
    # for any Profinet DCP replies (see filters).
    listener = AsyncSniffer(iface=iface, lfilter=lfilter, # stop_filter=lfilter,
                            timeout=timeout)#, prn=lambda x: x.summary())
    listener.start()
    sendp(packet, iface=iface, verbose=False)
    listener.join()
    replies = listener.results # Responses + sniffed Profinet packets
    devices = []
    for reply in replies:
        devices.append(ProfinetDevice(reply[1]))
    return devices
