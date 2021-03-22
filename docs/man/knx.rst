KNX
===

KNX is a field bus protocol, mainly used for building management systems. BOF
implements KNXnet/IP, which is part of the KNX specification to link field KNX
components to the IP network.

.. code-block::

   from bof import knx

Discover KNX devices
--------------------

The function `search()` from `bof.knx` lists the IP addresses of KNX devices
responding on an IP network.

>>> from bof import knx
>>> knx.search("192.168.1.0/24")
['192.168.1.10']

The function `discover()` gathers information about a KNX device at a defined IP
address (or on multiple KNX devices on an address range) and stores it to a
``KnxDevice`` object.

>>> from bof import knx
>>> device = knx.discover("192.168.1.10")
>>> print(device)
KnxDevice: Name=boiboite, MAC=00:00:54:ff:ff:ff, IP=192.168.1.10:3671 KNX=15.15.255

Connect to a device
-------------------

.. code-block:: python

   from bof import knx, BOFNetworkError

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

> TODO

Understanding KNX frames
------------------------

Conforming to the KNX Standard v2.1, a KNX frame has a header and body. The
header's structure never changes but the body's structure varies according to
the type of frame (message) given in the header's ``service identifier``
field.

.. figure:: images/knx_frame.png

> TODO

Create frames
-------------

> TODO

Modify frames
-------------

> TODO

.. warning::

   KNX frame servers usually have strict parsing rules and won't consider
   invalid frames. If you modify the structure of a frame or block and differ
   too much from the specification, you should not expect the KNX device to
   respond.
