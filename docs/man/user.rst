Overview
========

BOF (Boiboite Opener Framework) is a testing framework for field protocols
implementations and devices. It is a Python 3.6+ library that provides means to
send, receive, create, parse and manipulate frames from supported protocols.

The library currently supports **KNXnet/IP**, which is our focus, but it can be
extended to other types of BMS or industrial network protocols.

There are three ways to use BOF:

* Automated: Use of higher-level interaction functions to discover devices and
  start basic exchanges, without requiring to know anything about the protocol.

* Standard: Perform more advanced (legitimate) operations. This requires the end
  user to know how the protocol works (how to establish connections, what kind
  of messages to send).

* Playful: Modify every single part of exchanged frames and misuse the protocol
  instead of using it (we fuzz devices with it). The end user should have
  started digging into the protocol's specifications.

.. figure:: images/bof_levels.png

**Please note that targeting BMS systems can have a severe impact on buildings and
people and that BOF must be used carefully.**

TL;DR
=====

Clone repository::

    git clone https://github.com/Orange-Cyberdefense/bof.git

BOF is a Python 3.6+ library that should be imported in scripts.  It has no
installer yet so you need to refer to the `bof` subdirectory which contains the
library (inside the repository) in your project or to copy the folder to your
project's folder. Then, inside your code (or interactively):

.. code-block:: python

   import bof

Now you can start using BOF!

The following code samples interact using the building management system
protocol KNXnet/IP (the framework supports only this one for now).

Discover devices on a network
-----------------------------

>>> from bof import knx
>>> knx.search("192.168.1.0/24")
['192.168.1.10']

>>> from bof import knx
>>> device = knx.discover("192.168.1.10")
>>> print(device)
KnxDevice: Name=boiboite, MAC=00:00:54:ff:ff:ff, IP=192.168.1.10:3671 KNX=15.15.255

Send and receive packets
------------------------

.. code-block:: python

   from bof import knx, BOFNetworkError

   knxnet = knx.KnxNet()
   try:
       knxnet.connect("192.168.1.1", 3671)
       frame = knx.KnxFrame(type="DESCRIPTION REQUEST")
       print(frame)
       knxnet.send(frame)
       response = knxnet.receive()
       print(response)
   except BOFNetworkError as bne:
       print(str(bne))
   finally:
       knxnet.disconnect()

Craft your own packets!
-----------------------

.. code-block:: python

   from bof import knx

   frame = knx.KnxFrame()
   frame.header.service_identifier.value = b"\x02\x03"
   hpai = knx.KnxBlock(type="HPAI")
   frame.body.append(hpai)
   print(frame)

----------------------

Basic usage
===========

Library content
---------------

.. code-block:: python

    import bof
    from bof import byte
    from bof import knx
    from bof import knx, BOFNetworkError

Global module content can be imported directly from ``bof``. Protocol-specific
content is in specific submodules (ex: ``bof.knx``).

Network connection
------------------

BOF provides core class for TCP and UDP network connections, however they should
not be used directly, but inherited in protocol implementation network
connection classes (ex: ``KnxNet`` inherits ``UDP``). A connection class carries
information about a network connection and method to manage connection and
exchanges, that can vary depending on the protocol.

Here is an example on how to establish connection using the ``knx`` submodule
(``3671`` is the default port for KNXnet/IP).

.. code-block:: python

   knxnet = knx.KnxNet()
   try:
       knxnet.connect("192.168.1.1", 3671)
       knxnet.send(knx.KnxFrame(type="DESCRIPTION REQUEST"))
       response = knxnet.receive()
   except BOFNetworkError as bne:
       print(str(bne))
   finally:
       knxnet.disconnect()

Frames in BOF
-------------

Network frames are sent and received as byte arrays. They can be divided into a
set of blocks, which contain a set of fields of varying sizes.

In BOF, frames, blocks and fields are represented as objects (classes). A frame
(``BOFFrame``) has a header and a body, both of them being blocks
(``BOFBlock``).  A block contains a set of raw fields (``BOFField``) and/or
nested ``BOFBlock`` objects with a special structure.

Implementations inherit from these objects to build their own
specification-defined frames. They are described in BOF in a JSON specification
file, containing the definition of message codes, block types and frame
structures. The JSON file can change from one protocol to another but we
recommend that protocol use a basis (details are in the developer's manual).

The class ``BOFSpec``, inherited in implementations, is a singleton class to
parse and store specification JSON files. This class is used in
protocol implementations, mainly to build frames, but one can also refer to
it in scripts.

Code sample using KnxSpec:

>>> knx.KnxSpec().codes["service identifier"]
{'0000': 'EMPTY', '0201': 'SEARCH REQUEST', '0202': 'SEARCH RESPONSE', '0203':
'DESCRIPTION REQUEST', '0204': 'DESCRIPTION RESPONSE', '0205': 'CONNECT
REQUEST', '0206': 'CONNECT RESPONSE', '0207': 'CONNECTIONSTATE REQUEST', '0208':
'CONNECTIONSTATE RESPONSE', '0209': 'DISCONNECT REQUEST', '020A': 'DISCONNECT
RESPONSE', '0310': 'CONFIGURATION REQUEST', '0311': 'CONFIGURATION ACK'}

Error handling and logging
--------------------------

BOF has custom exceptions inheriting from a global custom exception class
``BOFError`` (code in `bof/base.py`):

:BOFLibraryError: Library, files and import-related exceptions.
:BOFNetworkError: Network-related exceptions (connection errors, etc.).
:BOFProgrammingError: Misuse of the framework.

.. code-block:: python

   try:
       knx.connect("invalid", 3671)
   except bof.BOFNetworkError as bne:
       print("Connection failure: ".format(str(bne)))

Logging features can be enabled for the entire framework. Global events will be
stored to a file (default name is ``bof.log``). One can make direct call to
bof's logger to record custom events.

.. code-block:: python

    bof.enable_logging()
    bof.log("Cannot send data to {0}:{1}".format(address[0], address[1]), level="ERROR")

Other useful stuff
------------------

The framework comes with some useful functions used within the library but that can
be used in scripts as well. Refer to source code documentation for details.

:Byte conversion: `bof/byte.py` contains functions for byte resize and
		  conversion to/from int, string, ipv4, bit list.

.. code-block:: python

   x = bof.byte.from_int(1234)
   x = bof.byte.resize(x, 1) # Truncates
