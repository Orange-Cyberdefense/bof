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

Discover devices on a network
-----------------------------

> TODO

Send and receive packets
------------------------

> TODO

Craft your own packets!
-----------------------

> TODO

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

> TODO

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
