"""
Profinet DCP
------------

Profinet DCP (Discovery and Configuration Protocol) can be, as its name
suggests, used for network discovery directly on the Ethernet link.

BOF uses it for network discovery purposes in higher-level purposes. The
implementation is imcomplete, as we only use it as a support protocol (no
extended research or fuzzing intended so far).

Contents:

:profinet_functions: Send and receive Profinet DCP identify requests.
:profinet_devices: Object representation of a Profinet device.
:profinet_constants: Protocol-related constants.

Uses Scapy's Profinet IO contrib by Gauthier Sebaux and Profinet DCP contrib
by Stefan Mehner (stefan.mehner@b-tu.de).
"""

from .profinet_constants import *
from .profinet_device import *
from .profinet_functions import *
