"""
Module: Discovery
-----------------

Functions for passive and active discovery of industrial devices on a network.
"""

from os import geteuid
from time import sleep
from packaging.version import parse as version_parse
from ipaddress import IPv4Address
from scapy import VERSION as scapy_version
from scapy.layers.l2 import Ether, srp
from scapy.sendrecv import AsyncSniffer
from scapy.packet import Packet
# Internal
from .. import BOFProgrammingError, BOFDevice, DEFAULT_IFACE
from ..layers.knx import MULTICAST_ADDR as KNX_MULTICAST_ADDR, KNX_PORT, \
    search as knx_search

########################################################
# proto-related code will be moved to dedicated layer. #
# Todo when completed and fully tested.                #
# Unit tests to write after moving proto               #
########################################################

# LLDP -----------------------------------------------------------------------#

from scapy.contrib.lldp import *

LLDP_MULTICAST_MAC = "01:80:c2:00:00:0e"
LLDP_DEFAULT_TIMEOUT = 20
LLDP_DEFAULT_PARAM = {
    "chassis_id": "BOF",
    "port_id": "port-BOF",
    "ttl": 20,
    "port_desc": "BOF discovery",
    "system_name": "BOF",
    "system_desc": "BOF discovery"
    }

class LLDPDevice(BOFDevice):
    """Object representation of a device responding to LLDP requests."""
    # TODO: Change some name to match BOFDevice naming.
    protocol:str = "LLDP"
    mac_address: str = None
    chassis_id: str = None
    port_id: str = None
    port_desc: str = None
    system_name: str = None
    system_desc: str = None
    capabilities: dict = None
    ip_address: str = None
    
    def __init__(self, pkt: Packet=None):
        if pkt:
            self.parse(pkt)

    def parse(self, pkt: Packet=None) -> None:
        """Parse LLDP response to store device information.

        :param pkt: LLDP packet, including Ethernet (Ether) layer.

        Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
        """
        self.mac_address = pkt["Ether"].src
        self.chassis_id = pkt["LLDPDUChassisID"].id
        self.port_id = pkt["LLDPDUPortID"].id
        self.port_desc = pkt["LLDPDUPortDescription"].description.decode('utf-8')
        self.system_name = pkt["LLDPDUSystemName"].system_name.decode('utf-8')
        self.system_desc = pkt["LLDPDUSystemDescription"].description.decode('utf-8')
        self.capabilities = pkt["LLDPDUSystemCapabilities"] # TODO
        try: # TODO: Subtypes, we only handle IPv4 so far...
            self.ip_address = IPv4Address(pkt["LLDPDUManagementAddress"].management_address)
            # IP address as a property so that we can return it only if subtype==IPv4
        except AddressValueError as ave:
            raise BOFProgrammingError("Subtypes other than IPv4 not implemented yet.")
        # TODO: Profibus stuff (e.g. for Siemens devices)

    def __str__(self):
        return "[LLDP] Device {0} - {1}\n\tMAC address: {2}\n\tIP address: {3}".format(
            self.system_name, self.system_desc, self.mac_address, self.ip_address)
        
def create_lldp_packet(mac_addr: str=LLDP_MULTICAST_MAC, mgmt_ip: str="0.0.0.0",
                       lldp_param: dict=None) -> Packet:
    """Create a LLDP packet for discovery to be sent on Ethernet layer.

    :param mgmt_ip: Source IPv4 address to include as management address.
    :param lldp_param: Dictionary containing LLDP info to set. Optional.

    Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
    """
    # Dirty conversion from IP to hex, can be improved
    iphex = b''.join([int(i).to_bytes(1, byteorder="big") for i in mgmt_ip.split(".")])
    lldp_param = lldp_param if lldp_param else LLDP_DEFAULT_PARAM

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

    return Ether(type=0x88cc, dst=mac_addr)/LLDPDU()/lldp_chassisid/lldp_portid \
        /lldp_ttl/lldp_portdesc/lldp_sysname/lldp_sysdesc/lldp_capab \
        /lldp_mgmt/lldp_end

def send_lldp_request(iface: str=DEFAULT_IFACE, mac_addr:
                      str=LLDP_MULTICAST_MAC, mgmt_ip: str="0.0.0.0", lldp_param:
                      dict=None) -> None:
    """Send LLDP (Link Layer Discovery Protocol) packets on Ethernet layer.

    Multicast is used by default.
    Requires super-user privileges to send on Ethernet link.

    :param iface: Network interface to use to send the packet.
    :param mac_addr: MAC address to send the LLDP packet to (default: multicast)
    :param mgmt_ip: Source IPv4 address to include as management address.
    :param lldp_param: Dictionary containing LLDP info to set. Optional.

    Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
    """
    packet = create_lldp_packet(mac_addr, mgmt_ip, lldp_param)
    # Using Scapy's send function on Ethernet, requires super user privilege
    if geteuid() != 0:
        raise BOFProgrammingError("Super user privileges required to send LLDP requests")
    # Timeout should be high because devices take time to respond
    sendp(packet, multi=1, iface=iface, verbose=False)
    
def lldp_listen_start(iface: str=DEFAULT_IFACE,
                      timeout: int=LLDP_DEFAULT_TIMEOUT) -> AsyncSniffer:
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

def lldp_listen_stop(sniffer: AsyncSniffer) -> list:
    if sniffer.running:
        sniffer.stop()
    return sniffer.results

def lldp_listen_sync(iface: str=DEFAULT_IFACE, timeout: int=LLDP_DEFAULT_TIMEOUT) -> list:
    """Search for devices on an network by listening to LLDP requests.
    
    Converts back asynchronous to synchronous with sleep (silly I know).  If you
    want to keep asynchrone, call directly ``lldp_listen_start`` and
    ``lldp_listen_stop`` in your code.

    Implementation in LLDP layer.
    """
    sniffer = lldp_listen_start(iface, timeout)
    sleep(timeout)
    results = lldp_listen_stop(sniffer)
    devices = []
    for result in results:
        devices.append(LLDPDevice(result))
    return devices

# End of LLDP ----------------------------------------------------------------#

# Profinet - PN-DCP ----------------------------------------------------------#

if version_parse(scapy_version) <= version_parse("2.4.5"):
    # Layer pnio_dcp raises deprecation warnings for Scapy < 2.5.0
    from warnings import filterwarnings
    from cryptography.utils import CryptographyDeprecationWarning
    filterwarnings('ignore', category=SyntaxWarning)
    filterwarnings('ignore', category=CryptographyDeprecationWarning)
from scapy.contrib.pnio import ProfinetIO
from scapy.contrib.pnio_dcp import *

PNDCP_MULTICAST_MAC = "01:0e:cf:00:00:00"
PNDCP_DEFAULT_TIMEOUT = 10

class ProfinetDevice(BOFDevice):
    """Object representation of a device responding to PN-DCP requests."""
    # TODO: Change some name to match BOFDevice naming.
    protocol:str = "ProfinetDCP"
    name: str = None
    mac_address: str = None
    ip_address: str = None
    ip_netmask: str = None
    ip_gateway: str = None    
    device_vendor_value: str = None
    vendor_id: str = None
    device_id:str = None

    def __init__(self, pkt: Packet=None):
        if pkt:
            self.parse(pkt)
            
    def parse(self, pkt: Packet=None) -> None:
        self.name = pkt["DCPNameOfStationBlock"].name_of_station.decode('utf-8')
        self.mac_address = pkt["Ether"].src
        self.ip_address = pkt["DCPIPBlock"].ip
        self.ip_netmask = pkt["DCPIPBlock"].netmask
        self.ip_gateway = pkt["DCPIPBlock"].gateway
        self.device_vendor_value = pkt["DCPManufacturerSpecificBlock"].\
                                   device_vendor_value.decode('utf-8')
        self.vendor_id = pkt["DCPDeviceIDBlock"].vendor_id
        self.device_id = pkt["DCPDeviceIDBlock"].device_id

    def __str__(self):
        return "[Profinet] Device {0} - {1}\n\tMAC address: {2}\n\tIP address: {3}" \
            "\n\tNetmask: {4}\n\tGateway: {5}".format(
                self.name, self.device_vendor_value, self.mac_address, self.ip_address,
                self.ip_netmask, self.ip_gateway)
        
def create_pndcp_identify_packet(mac_addr: str=PNDCP_MULTICAST_MAC) -> Packet:
    """Create a Profinet DCP packet for discovery to be sent on Ethernet layer.

    Uses Scapy's Profinet IO contrib by Gauthier Sebaux and Profinet DCP contrib
    by Stefan Mehner (stefan.mehner@b-tu.de).
    """
    pn_io = ProfinetIO(frameID=DCP_IDENTIFY_REQUEST_FRAME_ID)
    pn_dcp = ProfinetDCP(service_id="Identify", service_type=DCP_REQUEST,
                         option=255, sub_option=255, dcp_data_length=4)
    pkt = Ether(dst=mac_addr)/pn_io/pn_dcp
    return pkt

def pndcp_identify_request(iface: str=DEFAULT_IFACE,
                           mac_addr: str=PNDCP_MULTICAST_MAC,
                           timeout: int=PNDCP_DEFAULT_TIMEOUT) -> list:
    """Send PN-DCP (Profinet Discovery/Config Proto) packets on Ethernet layer.

    Some industrial devices such as PLCs respond to them.
    Multicast is used by default.
    Requires super-user privileges to send on Ethernet link.

    :param iface: Network interface to use to send the packet.
    :param mac_addr: MAC address to send the PN-DCP packet to (default: multicast)

    Example::

      from bof.modules.discovery import *

      devices = pndcp_identify_request()
      for device in devices:
        print(device)

    Uses Scapy's Profinet IO contrib by Gauthier Sebaux and Profinet DCP contrib
    by Stefan Mehner (stefan.mehner@b-tu.de).
    """
    packet = create_pndcp_identify_packet(mac_addr)
    # Using Scapy's send function on Ethernet, requires super user privilege
    if geteuid() != 0:
        raise BOFProgrammingError("Super user privileges required to send PN-DCP requests")
    replies, norep = srp(packet, multi=1, iface=iface, timeout=timeout, verbose=False)
    devices = []
    for reply in replies:
        devices.append(ProfinetDevice(reply[1]))
    return devices

# End of PN-DCP --------------------------------------------------------------#

###############################################################################
# LLDP                                                                        #
###############################################################################

def lldp_discovery(iface: str=DEFAULT_IFACE, timeout: int=LLDP_DEFAULT_TIMEOUT) -> list:
    """Search for devices on an network by listening to LLDP requests.
    
    Converts back asynchronous to synchronous with sleep (silly I know).  If you
    want to keep asynchrone, call directly ``lldp_listen_start`` and
    ``lldp_listen_stop`` in your code.

    Implementation in LLDP layer.
    """
    return lldp_listen_sync(iface, timeout)

###############################################################################
# PN-DCP                                                                      #
###############################################################################

def profinet_discovery(iface: str=DEFAULT_IFACE, mac_addr: str=PNDCP_MULTICAST_MAC) -> list:
    """Search for devices on an network using multicast Profinet DCP requests.

    Implementation in Profinet layer.
    """
    return pndcp_identify_request(iface, mac_addr)

###############################################################################
# KNX                                                                         #
###############################################################################

def knx_discovery(ip: str=KNX_MULTICAST_ADDR, port=KNX_PORT, **kwargs):
    """Search for KNX devices on an network using multicast.

    Implementation in KNX layer.
    """
    return knx_search(ip, port)

###############################################################################
# GLOBAL                                                                      #
###############################################################################

def passive_discovery(iface: str=DEFAULT_IFACE,
                      pndcp_multicast: str=PNDCP_MULTICAST_MAC,
                      knx_multicast: str=KNX_MULTICAST_ADDR,
                      verbose: bool=False):
    """Discover devices on an industrial network using passive methods.

    Requests are sent to protocols' multicast addresses or via broadcast.
    Currently, LLDP and KNX are supported.

    :param lldp_multicast: Multicast MAC address for LLDP requests.
    :param knx_multicast: Multicast IP address for KNXnet/IP requests.
    """
    vprint = lambda msg: print("[BOF] {0}.".format(msg)) if verbose else None
    protocols = {
        # Protocol name: [Discovery function, Multicast address]
        # "LLDP": [lldp_discovery, lldp_multicast],
        "Profinet": [profinet_discovery, pndcp_multicast],
        "KNX": [knx_discovery, knx_multicast]
    }
    total_devices = []
    # Start async sniffing
    vprint("Listening to LLDP requests...")
    lldp_sniffer = lldp_listen_start(iface)
    # Multicast requests send and receive
    for protocol, proto_args in protocols.items():
        discovery_fct, multicast_addr = proto_args
        vprint("Sending {0} request to {1}".format(protocol, multicast_addr))
        devices = discovery_fct(mac_addr=multicast_addr, iface=iface)
        nb = len(devices)
        vprint("{0} {1} {2} found".format(nb if nb else "No", protocol,
                                          "device" if nb <= 1 else "devices"))
        total_devices += devices
    # For now we need to wait a little longer to make sure we sniff something
    vprint("Still waiting for LLDP requests...")
    sleep(LLDP_DEFAULT_TIMEOUT - PNDCP_DEFAULT_TIMEOUT)
    # Stop async sniffing
    devices = lldp_listen_stop(lldp_sniffer)
    nb = len(devices)
    vprint("{0} {1} {2} found".format(nb if nb else "No", "LLDP",
                                      "device" if nb <= 1 else "devices"))
    total_devices += [LLDPDevice(device) for device in devices]
    # TODO: Merge devices based on their address but still keep all their
    # attributes from different device objects.
    for device in total_devices:
        vprint(device)
    return total_devices
