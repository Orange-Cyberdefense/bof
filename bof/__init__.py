"""
Boiboite Opener Framework
=========================

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

:layers:
    Protocol implementations to be imported in BOF. Importing ``layers`` gives
    acces to BOF protocol implementations as well as raw Scapy implementations
    (if any) in folder ``layers/scapy``.
"""

###############################################################################
# Include content to be imported by module users                              #
###############################################################################

from .base import *
from .network import *
from .packet import *
from .layers import *
