"""
Using layers
============

BOF relies on protocol implementations built using the Scapy syntax, to provide
security testing and fuzzing features. In other words, BOF works as follows:

.. code-block::

   End user
      |
      | makes call to
      v
   BOF protocol layer (ex: from bof.layers import knx)
      |
      | relies on
      v
   Scapy protocol implementation

The ``layers`` folder contain BOF features for implemented protocols.

Scapy protocol implementations can be imported directly from Scapy or from
a KNX implementation not integrated to Scapy that should be located in the 
``layers/raw_scapy`` folder.

.. code-block::

   from scapy.contrib import modbus
   from bof.layers.raw_scapy import knx
"""

from .knx import *
from .modbus import *
from .lldp import *
from .profinet import *
