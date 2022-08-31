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
from scapy.layers.l2 import Ether, srp

if version_parse(scapy_version) <= version_parse("2.4.5"):
    # Layer pnio_dcp raises deprecation warnings for Scapy < 2.5.0
    from warnings import filterwarnings
    from cryptography.utils import CryptographyDeprecationWarning
    filterwarnings('ignore', category=SyntaxWarning)
    filterwarnings('ignore', category=CryptographyDeprecationWarning)
from scapy.contrib.pnio import ProfinetIO
from scapy.contrib.pnio_dcp import *

from ... import BOFProgrammingError, BOFDevice, DEFAULT_IFACE
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
            
    def parse(self, pkt: Packet=None) -> None:
        # Service ID should be Identify, Service type should be Response success
        if pkt["ProfinetDCP"].service_id != 0x05 or \
           pkt["ProfinetDCP"].service_type != 0x01:
            raise BOFProgrammingError("Expecting an identify response to create device object.")
        self.name = pkt["DCPNameOfStationBlock"].name_of_station.decode('utf-8')
        self.description = pkt["DCPManufacturerSpecificBlock"].\
                           device_vendor_value.decode('utf-8')
        if "Ether" in pkt:
            self.mac_address = pkt["Ether"].src
        self.ip_address = pkt["DCPIPBlock"].ip
        self.ip_netmask = pkt["DCPIPBlock"].netmask
        self.ip_gateway = pkt["DCPIPBlock"].gateway
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
                         option=255, sub_option=255, dcp_data_length=4)
    pkt = pn_io/pn_dcp
    return pkt

def send_identify_request(iface: str=DEFAULT_IFACE,
                          mac_addr: str=MULTICAST_MAC,
                          timeout: int=DEFAULT_TIMEOUT) -> list:
    """Send PN-DCP (Profinet Discovery/Config Proto) packets on Ethernet layer.

    Some industrial devices such as PLCs respond to them.
    Multicast is used by default.
    Requires super-user privileges to send on Ethernet link.

    :param iface: Network interface to use to send the packet.
    :param mac_addr: MAC address to send the PN-DCP packet to (default: multicast)
    :param timeout: Timeout for responses. More than 10s because some devices
                    take time to respond.
    """
    packet = Ether(dst=mac_addr)/create_identify_packet()
    # Using Scapy's send function on Ethernet, requires super user privilege
    if geteuid() != 0:
        raise BOFProgrammingError("Super user privileges required to send PN-DCP requests")
    replies, norep = srp(packet, multi=1, iface=iface, timeout=timeout, verbose=False)
    devices = []
    for reply in replies:
        devices.append(ProfinetDevice(reply[1]))
    return devices
