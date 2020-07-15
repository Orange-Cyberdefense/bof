"""
Boiboite Opener Framework / Ouvre-Boiboite Framework contains a set of features
to write scripts using industrial network protocols for test and attack
purposes.

The following submodules are available:

:base:
    Basic helpers for correct module usage (error handling, logging, some
    parsing features. Available from direct bof import (``import bof``).

:network:
    Global network classes, used by protocol implementations in submodules.
    The content of this class should not be used directly, unless writing a
    new protocol submodule. Available from direct bof import (``import bof``)

:frame:
    Generic frame representation as objects within BOF. Classes from this
    submodule should be inherited by protocol implementations, but they should
    not be used directly by the end user.

:byte:
    Set of functions for byte conversion and handling. Accessed via import of
    the byte submodule (``from bof import byte``).

:knx:
    Implementation of the BMS protocol KNX, relying on ``bof.UDP``. Provides
    classes and methods for sending and receiving KNX datagrams on the network
    over KNXnet/IP, and for reading and writing valid or invalid KNX
    frames.
"""

###############################################################################
# Include content to be imported by module users                              #
###############################################################################

from .base import *
from .network import *
from .frame import *
from .byte import * 
from .spec import *
