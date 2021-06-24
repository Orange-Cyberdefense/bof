Notice
======

This section is intended for contributors, either for improving existing parts
(core, existing implementation) or adding new protocol implementations.  Before
going further, please consider the following notice.

Code quality requirements
-------------------------

:Quality: 

   We like clean code and expect contributions to be PEP-8 compliant as much as
   possible (even though we don't test for it). New code should be readable easily
   and maintainable. And remember: if you need to use "and" while explaining what
   your function does, then you can probably split it.

:Genericity:

   Part of the code (the "core") is used by all protocol implementations.  When
   you add code to the core, please make sure that it does not cause issues in
   protocol-specific codes. Also, if you write or find out that code in
   implementations can be made generic and added to the core, feel free to do
   it.

:Unit tests:

   We use Python's ``unittest`` to write unit tests. When working on BOF, please
   write or update unit tests!  They are in ``tests/``. You can run all unit tests
   with: ``python -m unittest discover -s tests``.

Comments and documentation
--------------------------

:Docstrings:

  Modules, functions, classes, methods start with docstrings written in 
  ReStructuredText. Docstrings are extracted to build the ReadTheDocs source
  code documentation using Sphinx. We use a not-so-strict format, but you
  should at least make sure that docstrings are useful to the reader, contain
  the appropriate details and have a valid and consistent format. You can also
  rely on the following model::

    """Brief description of the module, function, class, method.

    A few details on how, where, when and why to use it.

    :param first: Description of param "first": type, usage, origin
		  Second line of description if one isn't enough.
    :param second: Description of param "second"
    :returns: The value that is returned, if any.
    :raises BOFProgrammingError: if misused

    Usage example::

      if there is any interest in adding such example, please do so.
    """

Git branching
-------------

We follow the "successful git branching model" described `here
<https://nvie.com/posts/a-successful-git-branching-model/>`_. In a nutshell:

* Branch from ``master`` for hotfixes
* Work on ``dev`` for small changes
* Create specific ``feature`` branches from ``dev`` for big changes
* Don't work on ``master``

Report issues
-------------

Report bugs, ask questions or request for missing documentation and new features
by submitting an issue on GitHub. For bugs, please describe your problem as
clearly as you can.

Architecture
============

The library has the following structure::

  .
  ├── bof
  │   ├── base.py
  │   ├── network.py
  │   ├── packet.py
  │   ├── __init__.py
  │   ├── layers
  │   │   ├── knx
  │   │   │   ├── knx_feature.py
  │   │   │   ├── knx_network.py
  │   │   │   ├── knx_packet.py
  │   │   ├── other protocol
  │   │   │   ├── other protocol content
  │   │   └── raw_scapy
  │   │       ├── knx.py

* The protocol-independent part of BOF (the core) is in ``bof`` directly.
* BOF protocol features are in ``bof/layers/[protocol]``
* Scapy protocol implementations are imported directly from Scapy or can be
  stored in ``bof/layers/raw_scapy/[protocol].py``

Apart from the library:

* The documentation as RestructuredText files for Sphinx is in ``docs``
* Unit tests (one file for the core, one file per protocol) are in ``tests``
* Implementation examples are in ``examples/[protocol]``

Extend BOF
==========

Here is how to add a new protocol to BOF:

1. Make sure that the protocol exist in Scapy or provide an implementation in
   Scapy format (the file can be stored in ``bof/layers/raw_scapy``).
2. Create a folder in ``bof/layers`` with the name of your implementation. Here
   we'll add the protocol ``otter``.
3. In ``bof/layers/otter``, create a Python file with a class inerithing either
   from TCP or UDP (they are in ``bof/network.py``). It will contain any
   protocol-related operations at network level. For instance, you may overwrite
   send and receive operation so that they return ``OtterPacket`` directly.
4. Create another Python file to write a class ``OtterPacket`` (or whatever)
   inheriting from ``BOFPacket``.

.. code-block:: python

   class OtterPacket(BOFPacket):

5. Please refer to ``BOFPacket`` (in ``bof/packet.py``) and to other
   implementations such as ``KNX`` to know how to write the content of the
   class, until I write a better tutorial! :D
