"""
LLDP
----

LLDP (Link Layer Discovery Protocol) is, as its name suggests, used for network
discovery directly on the Ethernet link.

BOF uses it for network discovery purposes in higher-level purposes. The
implementation is imcomplete, as we only use it as a support protocol (no
extended research or fuzzing intended).

Contents:

:lldp_functions: LLDP listen, send, create and device representation.
:lldp_constants: Protocol-related constants.

Uses Scapy's LLDP contrib by Thomas Tannhaeuser (hecke@naberius.de).
"""

from .lldp_constants import *
from .lldp_functions import *
