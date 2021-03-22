"""
Package overview
================

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

:byte:
    Set of functions for byte conversion and handling. Accessed via import of
    the byte submodule (``from bof import byte``).
"""

###############################################################################
# Include content to be imported by module users                              #
###############################################################################

from .base import *
from .network import *
# from .byte import * 
