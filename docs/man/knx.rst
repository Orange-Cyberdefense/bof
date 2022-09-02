KNX
===

KNX is a field bus protocol, mainly used for building management systems. BOF
implements KNXnet/IP, which is part of the KNX specification to link field KNX
components to the IP network.

.. code-block::

   from bof.layers import knx

Device discovery
----------------

BOF provides features to discover devices on a network and gather information
about them. Calling them will send the appropriate KNXnet/IP requests to devices
and parse their response, you don't need to know how the protocol works.

.. code-block:: python

   from bof.layers.knx import search

   devices = search()
   for device in devices:
       print(device)

You can also learn more about a specific device:

.. code-block:: python

   from bof.layers.knx import discover

   device = discover("192.168.1.42")
   print(device)

The resulting object is a ``KNXDevice`` object that comes with a set
of attributes and methods to interact with a device.

.. note:: The function ``knx_discovery()`` in the **Discovery** module can also
	  be used (relies on ``search()``).

Send commands
-------------

A few commands are available so far to perform basic operations on a KNXnet/IP
server or underlying devices:

.. code-block:: python

   from bof.layers.knx import group_write

   # Write value 1 to group address 1/1/1
   group_write(device.ip_address, "1/1/1", 1)

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
``init`` parameter.

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
device. Frames are sent and received as byte arrays, but they are represented as
``KNXPacket`` within BOF. In the example above, we create a frame with type
``Description Request`` to ask a device to describe itself. The format of such
frame is extracted from the KNX implementation in Scapy format, either
integrated to Scapy or imported to BOF's ``raw_scapy`` directory. The
``response`` is received as a byte array, converted to a ``KNXPacket`` object.

You can also use methods that will directly initialize and send the following
basic KNXnet/IP frames.

.. code-block:: python

    knxnet = KNXnet().connect(ip, port)
    # CONNECT REQUEST
    channel = connect_request_management(knxnet)
    # CONFIGURATION REQUEST with "property read" KNX message
    cemi = cemi_property_read(CEMI_OBJECT_TYPES.ip_parameter_object,
                            CEMI_PROPERTIES.pid_additional_individual_addresses)
    response = configuration_request(knxnet, channel, cemi)
    # DISCONNECT REQUEST
    disconnect_request(knxnet, channel)
    knxnet.disconnect()

Available requests (from KNX Standard v2.1) are:

- ``Search request``
- ``Description request``
- ``Connect request`` (with connection type "management" and "tunneling")
- ``Disconnect request``
- ``Configuration request``
- ``Tunneling request``

.. note:: Configuration requests and tunneling requests "carry"
	  medium-independent KNX data in a block called "cEMI". Therefore, when
	  creating such a request you need to specify the type of cEMI to use
	  (see below for details).

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
contains a Scapy ``Packet`` with ``Field`` objects. Some ``Field`` objects act
as blocks (yeah, I know...) and may contain other ``Field`` objects.

Message types
+++++++++++++

The KNX standard describes a set of message types with different format. Please
refer to KNX implementation using Scapy here: ``bof/layers/raw_scapy/knx.py`` or
in Scapy's KNX contrib (should be the same anyway). The header contains a field
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

We use BOF to interact with a device over IP, that's why we always send
KNXnet/IP requests. Some of them stick to "IP" level and will retrieve global
information that "exist" at this level (for instance, hardware and network
information about a KNXnet/IP server).

.. code-block:: python

   knx.discover("192.168.1.42")

Outputs::

   Device: "boiboite" @ 192.168.1.242:3671 - KNX address: 15.15.255 -
   Hardware: 00:00:ff:ff:ff:ff (SN: 0123456789)

However, some requests move to the "KNX" level (the layer below), either to
retrieve or send KNX-specific information on a KNXnet/IP server, or to interact
with KNX devices underneath. In this case, some KNXnet/IP frames (most notably
configuration requests and tunneling requests) will carry a special block
containing medium-independent KNX data.

This special KNX data block is called cEMI (for Common External Messaging
Interface) and it acts like a frame inside the frame, with its own protocol
definition. You can also find it in KNX standard v2.1, but KNXnet/IP
specification is not the same as KNX specification.

For instance, "tunneling requests" carry KNX data to be transferred to KNX
devices. When you want to write a value to a KNX object, the tunneling request
has to carry a specific cEMI message for value write on addresses.

This cEMI message has a type (here, the data link layer message format) and a
set of properties of values to indicate what is the expected behavior.

Here is one way to write a KNX write request on a group address with BOF. There
are higher-level functions in BOF to do the same thing.  For this one you can
also just call the ``group_write()`` function.

.. code-block:: python

   # Create cEMI block (KNX data)
   cemi = scapy_knx.CEMI(message_code=CEMI.l_data_req) # Link layer request
   cemi.cemi_data.source_address = knx_source # Retrieved from a connect request
   cemi.cemi_data.destination_address = "1/1/1"
   cemi.cemi_data.acpi = ACPI.groupvaluewrite # Type of command
   cemi.cemi_data.data = value
   # Insert it to a tunneling request
   tun_req = KNXPacket(type=SID.tunneling_request)
   tun_req.communication_channel_id = channel # Retrieved from a connect request
   tun_req.cemi = cemi
   tun_req.show2()

.. code-block::

   ###[ KNXnet/IP ]### 
    header_length= 6
    protocol_version= 0x10
    service_identifier= TUNNELING_REQUEST
    total_length= 21
   ###[ TUNNELING_REQUEST ]### 
     structure_length= 4
     communication_channel_id= 1
     sequence_counter= 0
     reserved  = 0
     \cemi      \
      |###[ CEMI ]### 
      |  message_code= L_Data.req
      |  \cemi_data \
      |   |###[ L_cEMI ]### 
      |   |  additional_information_length= 0
      |   |  additional_information= ''
      |   |  frame_type= standard
      |   |  reserved  = 0
      |   |  repeat_on_error= 1
      |   |  broadcast_type= domain
      |   |  priority  = low
      |   |  ack_request= 0
      |   |  confirmation_error= 0
      |   |  address_type= group
      |   |  hop_count = 6
      |   |  extended_frame_format= 0
      |   |  source_address= 15.15.255
      |   |  destination_address= 1/1/1
      |   |  npdu_length= 1
      |   |  packet_type= data
      |   |  sequence_type= unnumbered
      |   |  reserved  = 0
      |   |  acpi      = GroupValueWrite
      |   |  data      = 1


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
