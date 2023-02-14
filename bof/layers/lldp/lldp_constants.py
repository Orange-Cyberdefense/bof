"""
LLDP constants
--------------

Protocol-dependent constants (network and functions) for LLDP.
"""

from scapy.contrib.lldp import LLDPDUGenericOrganisationSpecific

LLDP_MULTICAST_MAC = MULTICAST_MAC = "01:80:c2:00:00:0e"
LLDP_DEFAULT_TIMEOUT = DEFAULT_TIMEOUT = 30
LLDP_DEFAULT_TTL = DEFAULT_TTL = 20

LLDP_DEFAULT_PARAM = DEFAULT_PARAM = {
    "chassis_id": "BOF",
    "port_id": "port-BOF",
    "ttl": DEFAULT_TTL,
    "port_desc": "BOF discovery",
    "system_name": "BOF",
    "system_desc": "BOF discovery",
    "management_address": "0.0.0.0"
}

LLDP_ORG_CODES = ORG_CODES = LLDPDUGenericOrganisationSpecific.ORG_UNIQUE_CODES
