"""
Introduction
============

Boiboite Opener Framework / Ouvre-Boiboite Framework contains a set of features
to write scripts using industrial network protocols for test and attack
purposes.

The following submodules are available:

:base:
    Basic helpers for correct module usage (error handling, logging, some
    parsing features.

:network:
    Global network classes, used by protocol implementations in submodules.
    The content of this class should not be used directly, unless writing a
    new protocol submodule.

:packet:
    Base classe for specialized BOF packets in layers. Such classes link BOF
    content and usage to protocol implementations in Scapy. In other words,
    they interface BOF's syntax used by the end user with Scapy Packet and
    Field objects used for the packet itself. The base class ``BOFPacket``
    is not supposed to be instantiated directly, but whatever. 

:layers:
    Protocol implementations to be imported in BOF. Importing ``layers`` gives
    acces to BOF protocol implementations inheriting from ``BOFPacket``
    (interface between BOF and Scapy worlds).  The directory
    ``layers/raw_scapy`` may contain protocol implementations in Scapy which
    are not integrated to Scapy's repository (for instance, if you wrote your
    own but did not contribute (yet)).
"""

###############################################################################
# Include content to be imported by module users when importing "bof"         #
###############################################################################

from .base import *
from .network import *
from .packet import *
from .layers import *
