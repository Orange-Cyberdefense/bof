"""Introduction
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
    Base class for specialized BOF packets in layers. Such classes link BOF
    content and usage to protocol implementations in Scapy. In other words,
    they interface BOF's syntax used by the end user with Scapy Packet and
    Field objects used for the packet itself. The base class ``BOFPacket``
    is not supposed to be instantiated directly, but whatever. 

:device:
    Global object for representing industrial devices. All objects in
    layers built using data extracted from responses to protocol-specific
    discovery requests shall inherit ``BOFDevice``.

:layers:
    Protocol implementations to be imported in BOF. Importing ``layers`` gives
    access to BOF protocol implementations inheriting from ``BOFPacket``
    (interface between BOF and Scapy worlds).  The directory
    ``layers/raw_scapy`` may contain protocol implementations in Scapy which
    are not integrated to Scapy's repository (for instance, if you wrote your
    own but did not contribute (yet)).

:modules:
    Higher level functions gathered around a specific usage that may rely on
    several protocols (layers).

"""

###############################################################################
# Include content to be imported by module users when importing "bof"         #
###############################################################################

from .base import *
from .network import *
from .packet import *
from .device import *
from .layers import *
from .modules import *
