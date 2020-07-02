"""
KNXnet/IP protocol implementation for Building Management System (BMS).

The implementation schemes and frame descriptions are based on **KNX Standard**
**v2.1 03_08_01**. The specification is described in :file:`knxnet.json`.

A user should be able to create or alter any frame to both valid and invalid
format. Therefore, a user can copy, modify or replace the specification file to
include or change any content they want.

The ``knx`` submodule has the following content:

:knxnet:
    Class for network communication with KNX. Connect, disconnect, send and
    receive KNX frames to and from KNX gateways and objects. Available from
    direct import of the ``knx`` submodule (``from bof import knx``).

:knxframe:
    Object representations of KNX frames and frame content (blocks and
    fields) and specification details, with methods to build, alter or read
    a frame or part of it. Available from direct import of the ``knx``
    submodule (``from bof import knx``).
"""

from .knxnet import *
from .knxframe import *
from .knxdevice import *
