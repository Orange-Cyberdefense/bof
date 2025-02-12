"""
Profinet DCP functions
----------------------

Object representation of a device discovered via PNDCP.

Uses Scapy's Profinet IO contrib by Gauthier Sebaux and Profinet DCP contrib
by Stefan Mehner (stefan.mehner@b-tu.de).
"""

# Scapy
from scapy.packet import Packet
from scapy.contrib.pnio_dcp import *

# Internal
from ... import BOFDevice, BOFProgrammingError
from .profinet_constants import *

#-----------------------------------------------------------------------------#
# PNDCP device                                                                #
#-----------------------------------------------------------------------------#

class ProfinetDevice(BOFDevice):
    """Object representation of a device responding to PN-DCP requests."""
    protocol:str = "ProfinetDCP"
    # Specific
    description: str = None # device_vendor_value
    mac_address: str = None
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
            # TODO : The second part of the condition was commented and I
            # re-introduced it for test_0301_pndcp_device_raise, keep an eye on it
            if pkt["ProfinetDCP"].service_id != SERVICE_ID_IDENTIFY or \
               pkt["ProfinetDCP"].service_type != SERVICE_TYPE_RESPONSE_SUCCESS:
                raise BOFProgrammingError(
                    "Expecting an identify response to create device object.")
        # Sometimes everything is in the ProfinetDCP frame directly, we extract data based on options
        if pkt["ProfinetDCP"].option == 0x02 and \
           pkt["ProfinetDCP"].sub_option in [0x02, 0x06]:
            option = DCP_SUBOPTIONS[pkt["ProfinetDCP"].option][pkt["ProfinetDCP"].sub_option]
            self.name = getattr(pkt["ProfinetDCP"], to_property(option)).decode('utf-8')
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
        data = [super().__str__()]
        if self.description:
            data += ["\tDescription: {0}".format(self.description)]
        if self.mac_address:
            data += ["\tMAC Address: {0}".format(self.mac_address)]
        if self.ip_netmask:
            data += ["\tIP Netmask: {0}".format(self.ip_netmask)]
        if self.ip_gateway:
            data += ["\tIP Gateway: {0}".format(self.ip_gateway)]
        if self.vendor_id:
            data += ["\tVendor ID: {0}".format(self.vendor_id)]
        if self.device_id:
            data += ["\tDevice ID: {0}".format(self.device_id)]
        return "\t\n".join(data)
