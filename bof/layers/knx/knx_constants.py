"""
Profinet DCP constants
----------------------

Protocol-dependent constants (network and functions) for PNDCP.
"""

from ... import to_property
from ...layers.raw_scapy import knx as scapy_knx

KNX_MULTICAST_ADDR = MULTICAST_ADDR = "224.0.23.12"
KNX_PORT = PORT = 3671

# Converts Scapy KNX's SERVICE_IDENTIFIER_CODES & CEMI dicts with format
# {byte value: service name} to the opposite, so that the end user can call
# services by their names instead of their values.
SID = type('SID', (object,),
           {to_property(v):k.to_bytes(2, byteorder='big') \
            for k,v in scapy_knx.SERVICE_IDENTIFIER_CODES.items()})()
CEMI = type('CEMI', (object,),
           {to_property(v):k for k,v in scapy_knx.MESSAGE_CODES.items()})()
ACPI = type('ACPI', (object,),
           {to_property(v):k for k,v in scapy_knx.KNX_ACPI_CODES.items()})()

CONNECTION_TYPE_CODES = type('CONNECTION_TYPE_CODES', (object,),
                             {to_property(v):k for k,v in scapy_knx.CONNECTION_TYPE_CODES.items()})()
CEMI_OBJECT_TYPES = type('CEMI_OBJECT_TYPES', (object,),
                         {to_property(v):k for k,v in scapy_knx.CEMI_OBJECT_TYPES.items()})()

CEMI_PROPERTIES = type('CEMI_PROPERTIES', (object,),
                       {to_property(v):k for k,v in scapy_knx.CEMI_PROPERTIES.items()})()

TYPE_FIELD = "service_identifier"
CEMI_FIELD = "cemi"
