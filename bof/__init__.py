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

TL;DR
=====

Import the module and submodules::

    import bof
    from bof import byte

Error handling::

    try:
        knx.connect("invalid", 3671)
    except bof.BOFNetworkError as bne:
        print("Connection failure: ".format(str(bne)))

Logging::

    bof.enable_logging()
    bof.log("Cannot send data to {0}:{1}".format(address[0], address[1]), level="ERROR")

"""

###############################################################################
# Include content to be imported by module users                              #
###############################################################################

from .base import *
from .network import *
from .byte import * 
