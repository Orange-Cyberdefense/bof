"""
Overview
========

Boiboite Opener Framework / Ouvre-Boiboite Framework contains a set of features
to write scripts using industrial network protocols for test and attack
purposes. Functions/tools can be used for:

:Communication: Network connection, initialization and message exchange
                (send/receive)
:Analysis:      Parsing and use of received messages
:Crafting:      Messages forging (valid, invalid, malicious)
:Interaction:   Simple actions such as network discovery, flood, etc.
"""

###############################################################################
# Include content to be imported by module users                              #
###############################################################################

from .base import *
from .network import *
from .byte import * 
