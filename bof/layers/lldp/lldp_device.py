"""
LLDP device
-----------

Object representation of a device using the protocol LLDP.

Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
"""

from ipaddress import IPv4Address, AddressValueError

# Scapy
from scapy.packet import Packet
from scapy.contrib.lldp import *

# Internal
from ... import BOFDevice, BOFProgrammingError
from .lldp_constants import ORG_CODES

class LLDPDevice(BOFDevice):
    """Object representation of a device described LLDP requests."""
    protocol:str = "LLDP"

    # TODO : Refactoring
    @classmethod
    def init_from_packet(cls, pkt: Packet):
        """Parse LLDP response as Scapy packet to store device information.

        :param pkt: LLDP packet (Scapy), including Ethernet (Ether) layer.
        """
        name = ""
        description = ""
        mac_address = ""
        ip_address = ""
        chassis_id = ""
        port_id = ""
        port_desc = ""
        organisation = ""
        if pkt.haslayer(LLDPDUSystemName):
            name = pkt["LLDPDUSystemName"].system_name.decode('utf-8')
        if pkt.haslayer(LLDPDUSystemDescription):
            description = pkt["LLDPDUSystemDescription"].description.decode('utf-8')
        if "Ether" in pkt:
            mac_address = pkt["Ether"].src
        try: # TODO: Subtypes, we only handle IPv4 so far...
            if pkt.haslayer(LLDPDUManagementAddress):
                ip_address = IPv4Address(pkt["LLDPDUManagementAddress"].management_address)
            # IP address as a property so that we can return it only if subtype==IPv4
        except AddressValueError as ave:
            raise BOFProgrammingError("Subtypes other than IPv4 not implemented yet.")
        if pkt.haslayer(LLDPDUChassisID):
            chassis_id = pkt["LLDPDUChassisID"].id
            if not isinstance(chassis_id, str):
                chassis_id = chassis_id.decode('utf-8')
        if pkt.haslayer(LLDPDUPortID):
            port_id = pkt["LLDPDUPortID"].id
            if not isinstance(port_id, str):
                port_id = port_id.decode('utf-8')
        if pkt.haslayer(LLDPDUPortDescription):
            port_desc = pkt["LLDPDUPortDescription"].description.decode('utf-8')
        # if pkt.haslayer(LLDPDUSystemCapabilities):
        #     self.capabilities = pkt["LLDPDUSystemCapabilities"] # TODO
        if pkt.haslayer(LLDPDUGenericOrganisationSpecific):
            # We look for the name matching the code
            try:
                organisation = ORG_CODES[
                    pkt["LLDPDUGenericOrganisationSpecific"].org_code]
            except KeyError: # Code not found, use value as is
                organisation = pkt["LLDPDUGenericOrganisationSpecific"].org_code
        args = {
            "name": name, "description": description, "mac_address": mac_address,
            "ip_address": ip_address, "chassis_id": chassis_id, "port_id": port_id,
            "port_desc": port_desc, "organisation": organisation
        }
        return cls(**args)
