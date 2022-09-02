"""
KNX and KNXnet/IP
-----------------

KNX is a common field bus protocol in Europe, mostly used in Building Management
Systems. KNXnet/IP is the version of the protocol over IP, implementing specific
type of frames that either ask information from or send request to a gateway
(server) between an IP network and a KNX bus or carry KNX messages that the
gateway must relay to KNX devieces on the field bus.

The protocol is a merge a several older ones, the specifications are maintained
by the KNX association and can be found on their website (section 3 is the
interesting one).

BOF's ``knx`` submodule can be imported with::

    from bof.layers import knx
    from bof.layers.knx import *

The following files are available in the module:

:knx_network:
    Class for network communication with KNX over UDP. Inherits from BOF's
    ``network`` ``UDP`` class. Implements methods to connect, disconnect and
    mostly send and receive frames as ``KNXPacket`` objects.

:knx_packet:
    Object representation of a KNX packet. ``KNXPacket`` inherits ``BOFPacket``
    and uses Scapy's implementation of KNX (located in ``bof/layers/raw_scapy``
    or directly in Scapy contrib). Contains method to build, read or alter a
    frame or part of it, even if this does not follow KNX's specifications.

:knx_messages:
    Set of functions that build specific KNX messages with the right values.

:knx_functions:
    Higher-level functions to discover and interact with devices via KNXnet/IP.
"""

from .knx_network import *
from .knx_packet import *
from .knx_messages import *
from .knx_functions import *
