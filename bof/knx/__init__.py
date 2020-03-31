"""
KNXnet/IP protocol implementation for Building Management System (BMS).

The implementation schemes and frame descriptions are based on **KNX Standard**
**v2.1 03_08_01**. The specification is described in :file:`knxnet.json`.

A user should be able to create or alter any frame to both valid and invalid
format. Therefore, a user can copy, modify or replace the specification file to
include or change any content they want.
"""

from .knxnet import *
from .knxframe import *
