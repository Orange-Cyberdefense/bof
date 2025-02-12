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
    name: str = None # system_name
    description: str = None # system_desc
    mac_address: str = None
    ip_address: str = None
    # LLDP specific
    chassis_id: str = None
    port_id: str = None
    port_desc: str = None
    capabilities: dict = None
    organisation: str = None
    
    def __init__(self, pkt: Packet=None):
        if pkt:
            self.parse(pkt)

    # TODO: Refactoring
    def parse(self, pkt: Packet=None) -> None:
        """Parse LLDP response to store device information.

        :param pkt: LLDP packet (Scapy), including Ethernet (Ether) layer.
        """
        if pkt.haslayer(LLDPDUSystemName):
            self.name = pkt["LLDPDUSystemName"].system_name.decode('utf-8')
        if pkt.haslayer(LLDPDUSystemDescription):
            self.description = pkt["LLDPDUSystemDescription"].description.decode('utf-8')
        if "Ether" in pkt:
            self.mac_address = pkt["Ether"].src
        try: # TODO: Subtypes, we only handle IPv4 so far...
            if pkt.haslayer(LLDPDUManagementAddress):
                self.ip_address = IPv4Address(pkt["LLDPDUManagementAddress"].management_address)
            # IP address as a property so that we can return it only if subtype==IPv4
        except AddressValueError as ave:
            raise BOFProgrammingError("Subtypes other than IPv4 not implemented yet.")
        if pkt.haslayer(LLDPDUChassisID):
            self.chassis_id = pkt["LLDPDUChassisID"].id
            if not isinstance(self.chassis_id, str):
                self.chassis_id = self.chassis_id.decode('utf-8')
        if pkt.haslayer(LLDPDUPortID):
            self.port_id = pkt["LLDPDUPortID"].id
            if not isinstance(self.port_id, str):
                self.port_id = self.port_id.decode('utf-8')
        if pkt.haslayer(LLDPDUPortDescription):
            self.port_desc = pkt["LLDPDUPortDescription"].description.decode('utf-8')
        # if pkt.haslayer(LLDPDUSystemCapabilities):
        #     self.capabilities = pkt["LLDPDUSystemCapabilities"] # TODO
        if pkt.haslayer(LLDPDUGenericOrganisationSpecific):
            # We look for the name matching the code
            try:
                self.organisation = ORG_CODES[
                    pkt["LLDPDUGenericOrganisationSpecific"].org_code]
            except KeyError: # Code not found, use value as is
                self.organisation = pkt["LLDPDUGenericOrganisationSpecific"].org_code

    def __str__(self):
        return "{0}\t\n\tDescription: {1}\n\tMAC address: {2}\n\t" \
            "Chassis ID: {3}\n\tPort ID: {4}\n\t" \
            "Port description: {5}\n\tOrganisation: {6}".format(
                super().__str__(), self.description, self.mac_address,
                self.chassis_id, self.port_id,
                self.port_desc, self.organisation)

