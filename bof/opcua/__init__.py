"""
OPC UA protocol implementation for industrial automation.

The implementation schemes and frame descriptions are based on **IEC 62541**
standard, **v1.04**. The specification is described in :file:`opcua.json`.

A user should be able to create or alter any frame to both valid and invalid
format. Therefore, a user can copy, modify or replace the specification file to
include or change any content they want.

The ``opcua`` submodule has the following content:

:opcuaframe:
    Object representations of OPC UA frames and frame content (blocks and
    fields) and specification details, with methods to build, alter or read
    a frame or part of it. Available from direct import of the ``opcua``
    submodule (``from bof import opcua``).
"""

from .opcuaframe import *
from .opcuanet import *

