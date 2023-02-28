"""
Profinet DCP functions
----------------------

Higher-level functions for network discovery using PNDCP.

Contents:

:PNDCPDevice:
    Object representation of a device discovered via PNDCP.
:Identify requests:
    Send and receive identify requests and response to discover devices.

Uses Scapy's Profinet IO contrib by Gauthier Sebaux and Profinet DCP contrib
by Stefan Mehner (stefan.mehner@b-tu.de).
"""

from os import geteuid
from time import sleep
from packaging.version import parse as version_parse

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

from ... import BOFProgrammingError, BOFDevice, DEFAULT_IFACE, to_property
from .profinet_constants import *

#-----------------------------------------------------------------------------#
# PNDCP device                                                                #
#-----------------------------------------------------------------------------#

class ProfinetDevice(BOFDevice):
    """Object representation of a device responding to PN-DCP requests."""
    protocol:str = "ProfinetDCP"
    name: str = None
    description: str = None # device_vendor_value
    mac_address: str = None
    ip_address: str = None
    # Specific
    ip_netmask: str = None
    ip_gateway: str = None    
    vendor_id: str = None
    device_id:str = None

    def __init__(self, pkt: Packet=None):
        if pkt:
            self.parse(pkt)

    # TODO: Refactoring
    def parse(self, pkt: Packet=None) -> None:
        if pkt.haslayer(ProfinetDCP):
            if pkt["ProfinetDCP"].service_id != SERVICE_ID_IDENTIFY:# or \
#               pkt["ProfinetDCP"].service_type != SERVICE_TYPE_RESPONSE_SUCCESS:
                raise BOFProgrammingError("Expecting an identify response to create device object.")
        # Sometimes everything is in the ProfinetDCP frame directly, we extract data based on options
        if pkt["ProfinetDCP"].option == 0x02 and pkt["ProfinetDCP"].sub_option in [0x02, 0x06]:
            option = DCP_SUBOPTIONS[pkt["ProfinetDCP"].option][pkt["ProfinetDCP"].sub_option]
            self.name = getattr(pkt["ProfinetDCP"], to_property(option))
        # And sometimes there are dedicated blocks...
        if pkt.haslayer(DCPNameOfStationBlock):
            self.name = pkt["DCPNameOfStationBlock"].name_of_station.decode('utf-8')
        elif pkt.haslayer(DCPAliasNameBlock):
            self.name = pkt["DCPAliasNameBlock"].alias_name.decode('utf-8')
        if pkt.haslayer(DCPManufacturerSpecificBlock):
            self.description = pkt["DCPManufacturerSpecificBlock"].\
                               device_vendor_value.decode('utf-8')
        if "Ether" in pkt:
            self.mac_address = pkt["Ether"].src
        if pkt.haslayer(DCPIPBlock):
            self.ip_address = pkt["DCPIPBlock"].ip
            self.ip_netmask = pkt["DCPIPBlock"].netmask
            self.ip_gateway = pkt["DCPIPBlock"].gateway
        if pkt.haslayer(DCPDeviceIDBlock):
            self.vendor_id = str(pkt["DCPDeviceIDBlock"].vendor_id)
            self.vendor_id = VENDOR[self.vendor_id] if self.vendor_id in \
                             VENDOR.keys() else "Unknown"
            self.device_id = pkt["DCPDeviceIDBlock"].device_id

    def __str__(self):
        return "{0}\n\tIP Netmask: {1}\n\tIP gateway: {2}\n\tVendor ID: {3}" \
            "\n\tDevice ID: {4}".format(
                super().__str__(), self.ip_netmask, self.ip_gateway, self.vendor_id, self.device_id)

#-----------------------------------------------------------------------------#
# Send PNDCP indentify packets on the network                                 #
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
    lfilter = lambda x: "Ether" in x and "ProfinetDCP" in x
    # We have to set a listener and not use srp in case the request is encapsulated
    # (Scapy does not detect it as a reply in this case). So we sniff the network
    # for any Profinet DCP replies (see filters).
    listener = AsyncSniffer(iface=iface, lfilter=lfilter, # stop_filter=lfilter,
                            timeout=timeout)#, prn=lambda x: x.summary())
    listener.start()
    # Issue to fix: we may sniff this packet as well (it appears as None)
    sendp(packet, iface=iface, verbose=False)
    listener.join()
    replies = listener.results # Responses + sniffed Profinet packets
    devices = []
    for reply in replies:
        devices.append(ProfinetDevice(reply[1]))
    return devices
