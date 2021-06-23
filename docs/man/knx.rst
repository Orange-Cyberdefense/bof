KNX
===

KNX is a field bus protocol, mainly used for building management systems. BOF
implements KNXnet/IP, which is part of the KNX specification to link field KNX
components to the IP network.

.. code-block::

   from bof.layers import knx

Connect to a device
-------------------

.. code-block:: python

   from bof.layers import knx
   from bof import BOFNetworkError

   knxnet = knx.KnxNet()
   try:
       knxnet.connect("192.168.1.1", 3671)
       # Do stuff
   except BOFNetworkError as bne:
       print(str(bne))
   finally:
       knxnet.disconnect()

The class ``KnxNet`` is used to connect to a KNX device (server or object). It
creates a UDP connection to a KNX device. ``connect`` can take an additionnal
``init`` parameter. When ``True``, a special connection request frame is sent to
the remote KNX device to agree on terms for the connection and "initializes" the
KNX exchange. This is required for some exchanges (ex: configuration requests),
but most requests can be sent without such initialization.

Send and receive frames
-----------------------

.. code-block:: python

  from bof.layers.knx import KNXnet, KNXPacket, SID

  knxnet = KNXnet().connect("192.168.1.242")
  pkt = KNXPacket(type=SID.description_request)
  pkt.ip_address, pkt.port = knxnet.source
  pkt.show2()
  response, _ = knxnet.sr(pkt)
  response.show2()
  knxnet.disconnect()

When a connection is established, one may start sending KNX frames to a
device. Frames are sent and received as byte arrays, bot they are represented as
``KNXPacket`` within BOF. In the example above, we create a frame with type
``Description Request`` to ask a device to describe itself. The format of such
frame is extracted from the KNX implementation in Scapy format, either
integrated to Scapy or imported to BOF's ``raw_scapy`` directory. The
``response`` is received as a byte array, converted to a ``KNXPacket`` object.

Understanding KNX frames
------------------------

Structure
+++++++++

Conforming to the KNX Standard v2.1, a KNX frame has a header and body. The
header's structure never changes but the body's structure varies according to
the type of frame (message) given in the header's ``service identifier``
field.

.. figure:: images/knx_frame.png

A KNX frame contains a set of blocks (set of fields) which contain raw fields or
nested block. In BOF (and Scapy), we do not refer to blocks: A ``KNXPacket``
contains a Scapy ``Packet`` with ``Field`` objects. SOme ``Field`` objects act
as blocks and may contain other ``Field`` objects.

Message types
+++++++++++++

The KNX standard describes a set of message types with different format. Please
refer to KNX implementation using Scapy here:
``bof/layers/raw_scapy/knx.py``. The header contains a field
``service_identifier`` that states the type of message. ``knx.SID`` contains a
list of valid types to use when creating a frame:

.. code-block:: python

   >>> from bof.layers.knx import *
   >>> packet = KNXPacket(type=SID.configuration_request)
   >>> packet.show2()
   ###[ KNXnet/IP ]### 
     header_length= 6
     protocol_version= 0x10
     service_identifier= CONFIGURATION_REQUEST
     total_length= 21
   ###[ CONFIGURATION_REQUEST ]### 
        structure_length= 4
        communication_channel_id= 1
        sequence_counter= 0
        reserved  = 0
        \cemi      \
         |###[ CEMI ]### 
         |  message_code= 0
         |  \cemi_data \
         |   |###[ L_cEMI ]### 
	 [...]

Service identifier codes are also directly accepted:

.. code-block:: python

   >>> packet2 = KNXPacket(type=0x0201)
   >>> packet2.show2()
   ###[ KNXnet/IP ]### 
     header_length= 6
     protocol_version= 0x10
     service_identifier= SEARCH_REQUEST
     total_length= 14
   ###[ ('SEARCH_REQUEST',) ]### 
        \discovery_endpoint\
         |###[ HPAI ]### 
         |  structure_length= 8
         |  host_protocol= IPV4_UDP
         |  ip_address= 0.0.0.0
         |  port      = 0

Specifying no types create an empty KNX Packet.

KNXnet/IP messages vs. KNX messages
+++++++++++++++++++++++++++++++++++

TODO

Testing KNXnet/IP implementations with BOF
------------------------------------------

BOF provides means to add fields, change their values, even if that does not
comply with the protocol.  Please refer to the protocol-independent
documentation to know how.

.. warning::

   KNX frame servers usually have strict parsing rules and won't consider
   invalid frames. If you modify the structure of a frame or block and differ
   too much from the specification, you should not expect the KNX device to
   respond.

TODO
