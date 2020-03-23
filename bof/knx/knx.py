"""
KNXnet/IP connection and frames implementations, implementing ``bof.network``'s
UDP classes.

Network connection
------------------

TODO

KNX frame handling
------------------

A KNX frame (datagram) is a byte array divided into a set of structures. A frame
always has the following format:

:Header: Single structure with basic data including the type of message.
:Content: One or more structures, depending on the type of message.

A structure (``KnxStructure``) is a byte array divided into a set of fields
(``KnxField``). A structure has the following data:

:Name: The name of the structure to be able to refer to it (using a property).
:Content: A set of fields and/or a set of sub-structures.

A field (``KnxField``) is a byte or a byte array with:

:Name: The name of the field to refer to it.
:Size: The number of bytes the field takes.
:Content: A byte or a byte array with the actual content.
"""

from enum import Enum
from os import path

from ..network import UDP, UDPStructure, UDPField
from ..base import BOFProgrammingError, load_json
