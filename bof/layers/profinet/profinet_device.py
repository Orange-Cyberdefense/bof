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

    # TODO: Refactoring
    @classmethod
    def init_from_packet(cls, pkt: Packet=None) -> None:
        name = ""
        description = ""
        mac_address = ""
        ip_address = ""
        ip_netmask = ""
        ip_gateway = ""
        vendor_id = ""
        device_id = ""
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
            name = getattr(pkt["ProfinetDCP"], to_property(option)).decode('utf-8')
        # And sometimes there are dedicated blocks...
        if pkt.haslayer(DCPNameOfStationBlock):
            name = pkt["DCPNameOfStationBlock"].name_of_station.decode('utf-8')
        elif pkt.haslayer(DCPAliasNameBlock):
            name = pkt["DCPAliasNameBlock"].alias_name.decode('utf-8')
        if pkt.haslayer(DCPManufacturerSpecificBlock):
            description = pkt["DCPManufacturerSpecificBlock"].\
                device_vendor_value.decode('utf-8')
        if "Ether" in pkt:
            mac_address = pkt["Ether"].src
        if pkt.haslayer(DCPIPBlock):
            ip_address = pkt["DCPIPBlock"].ip
            ip_netmask = pkt["DCPIPBlock"].netmask
            ip_gateway = pkt["DCPIPBlock"].gateway
        if pkt.haslayer(DCPDeviceIDBlock):
            vendor_id = str(pkt["DCPDeviceIDBlock"].vendor_id)
            vendor_id = VENDOR[vendor_id] if vendor_id in \
                VENDOR.keys() else "Unknown"
            device_id = pkt["DCPDeviceIDBlock"].device_id
        args = {
            "name": name, "description": description, "mac_address": mac_address,
            "ip_address": ip_address, "ip_netmask": ip_netmask, "ip_gateway": ip_gateway,
            "vendor_id": vendor_id, "device_id": device_id
        }
        return cls(**args)
