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
by submitting an issue with GitHub. For bugs, please describe your problem as
clearly as you can.

Architecture
============

The library has the following structure::

   ../bof
   ├── base.py
   ├── byte.py
   ├── frame.py
   ├── __init__.py
   ├── knx
   │   ├── __init__.py
   │   ├── knxdevice.py
   │   ├── knxframe.py
   │   ├── knxnet.json
   │   └── knxnet.py
   │── network.py
   └── spec.py

There is two distinct types of source files in BOF: The core content, used by
all implementations (in ``bof/``) and protocol-specific content, in subfolders
in ``bof/`` (ex: KNX implementation is in ``bof/knx/``).

Core components are described below. Main principles of protocol implementations
are described in the next section.

:Error and logging:

   ``base.py`` contains base exceptions classes for BOF and logging functions
   (based on ``logging``). Developer-defined exceptions can be added. They
   must inherit from base class ``BOFError``.

:Converters:

   Module ``byte`` contain byte-conversion functions that are used directly in
   protocol implementation classes. Any missing conversion class (from a type or
   from a specific format, such as IPv4) should be added here and not directly
   to implementations.

:Network connection:

   Basic class for TCP and UDP asynchronous network connection is in
   ``bof/network.py``. Such class should be used by protocol implementation's
   connection classes (ex: ``KnxNet`` inherits ``UDP``).

:Implementations base class:

   ``spec.py`` and ``frame.py`` contain base classes to use in implementation:
   specification file parsing base class, frame, block and field base classes.

Extend BOF
==========

BOF can (and should) be extended to other network protocols. If you feel like
contributing, here is how to start a new protocol implementation.

Source files tree
-----------------

The folder ``bof`` contains the library core functions. Subfolders, such as
``bof\knx`` contain implementations. Please create a new subfolder for your
implementation.

You should need 3 main components for a protocol implementation, described
below:

* A JSON file describing the protocol specification
* A connection class
* Frame, block and field building and parsing classes

Create the specification
------------------------

BOF parses a JSON file that explains how the library should create and parse
frames in a defined protocol. The main objective of using an external file is
not to bind the code too tightly to the specification (to change both of them
more easily). This JSON file is used within the code in a specification class
inheriting from ``BOFSpec``. It is recommended to build your own spec class and
to not use ``BOFSpec`` directly.

Write the JSON file
+++++++++++++++++++

The format of the JSON is "almost" up to you. We define 3 main categories that
BOF core can recognize, but you can add more or change them, as long as you
adapt the code in you subclasses. If you want not to rely on a JSON spec file,
you can, but you may loose all the benefits of using BOF :(

The JSON file should be in your protocol's subdirectory and we recommend that
you use the following base.

.. code-block:: json

   {
    "frame": [
        {"name": "header", "type": "HEADER"},
        {"name": "body", "type": "depends:message type"}
    ],
    "blocks": {
       "EMPTY": [
          {}
       ],
       "HEADER": [
          {"name": "header length", "type": "field", "size": 1, "is_length": true},
          {"name": "message type", "type": "field", "size": 1, "default": "01"},
          {"name": "total length", "type": "field", "size": 2}
       ],
       "HELLO": [
          {"name": "target otter", "type": "OTTER_DESC"}
       ],
       "OTTER_DESC": [
          {"name": "otter name", "type": "field", "size": 30},
          {"name": "age", "type": "field", "size": 1}
       ],
    },
    "codes" : {
       "message type": {
          "01": "HELLO"
       }
    }
   }

There are three categories in a specification JSON file:

:frame: The fixed definition of the frame format. For instance, many protocols
	have a frame with a fixed header and a varying body.
:blocks: The list of blocks (fixed set of fields and/or nested blocks. Blocks
	 can be complete frame body (ex: in the base JSON file, ``message type``
	 is used to choose the body) or part of another block.
:codes: Tables to match received codes as bytes arrays with block types (blocks)

.. warning::

   You are free to use them or not. However, if you do not follow this format
   you will have to create a class inheriting from ``BOFSpec`` in your protocol
   implementation and either add methods and code in your subclass if you add
   categories to the JSON file or overload methods from ``BOFSpec`` to change or
   remove the handling of these three default categories.

To sum up: 

* ``frame`` is the structure of the corresponding ``BOFFrame`` subclass
  of your implementation. each entry is added to the list of blocks contained
  in the frame.
* An entry is the definition of either a block with a specific type, referred by
  its name in the ``blocks`` category, or a ``field``. A block can contain as many
  nested blocks as required.
* The smallest item of a frame is a field, ``BOF`` will read blocks until it
  find fields. A field have a few mandatory parameters, and some optional ones.

:name: Mandatory name of the field
:size: Mandatory size of the field, in bytes
:type: ``field`` :)
:is_length: Optional boolean. If true, the value of this field is the size of
	    the block, and is updated when the block size changed 
:default: Default value, if no value has been specified before (by the user or
	  by parsing an existing frame).

Specification file parsing
++++++++++++++++++++++++++

Here is how the example JSON file above is used in the code:

The protocol implementation shall refer to ``BOFSpec`` or a subclass of
``BOFSpec`` that parses your JSON file.::

  class OtterSpec(BOFSpec):
     """Otter specification class, using the content of otter's JSON file."""
     def __init__(self, filepath:str=None):
        if not filepath:
           filepath = path.join(path.dirname(path.realpath(__file__)), "otter.json")
        super().__init__(filepath)

By default, your implementation's frame class inheriting from ``BOFFrame`` will
read the ``frame`` category. Here, the frame will have two main parts: a header
and a body.::

   {"name": "header", "type": "HEADER"},
   {"name": "body", "type": "depends:message type"}

We notice that ``header`` has type ``HEADER`` which is a type of block, defined
in the ``blocks`` category. The block ``header`` will then filled according th
the type defined and contain three fields.::

  "HEADER": [
     {"name": "header length", "type": "field", "size": 1, "is_length": true},
     {"name": "message type", "type": "field", "size": 1, "default": "01"},
     {"name": "total length", "type": "field", "size": 2}
  ]

A field has a set of attributes, discussed previously. When the frame is created
from the specification, blocks and fields are created but not filled, unless
there is a default value given (in command line or with the keyword ``default``
in the JSON file). When created from parsing a byte array, the fields are filled
directly with received bytes. The final header should look like this.::

  BOFBLock: header
     BOFField: header_length: b'\x04' (1 byte)
     BOFField: message_type: b'\x01' (1 byte)
     BOFField: total_length: b'\x00\x23' (2 byte)

The field ``total length`` is the complete size of the frame. You will have to
write some code in the frame to handle it, as well as any special field. Here is
an example from the ``KNX`` implementation::

  if "total_length" in self._blocks["header"].attributes:
     total = sum([len(block) for block in self._blocks.values()])
     self._blocks["header"].total_length._update_value(byte.from_int(total))

Now let's move to the body. Here, it contains only one block, but its content
changes entirely depending on the type of message: ``"type": "depends:message
type"``. This means that the parser will require the value of a field with name
``message type`` set previously (in the header, here). We'll need the category
``codes`` to match values with associated block types. ``codes`` is a dictionary
and each key is the name of a block. When extracting the value of ``message
type``, we'll search in ``codes["message type"]`` to know if there is a matching
block name for a value. If a value is ``\x01``, then the body block should be a
block ``HELLO``.::

  "codes" : {
     "message type": {
        "01": "HELLO"
     },
  }

The block type ``HELLO`` contains a block ``OTTER_DESC``, so we build it as well
as a nested block. The final body should look like this::

  BOFBLock: body
     BOFBlock: target otter
        BOFField: otter_name: b'seraph\x00\x00\x00 [...]' (30 bytes)
	BOFField: age: b'\x02' (1 byte)

Write connection classes
------------------------

Inheriting (or not) from ``UDP``, ``TCP`` or whatever from ``network.py``, it
(or they) should contain the protocol-specific connection steps. For instance,
if the protocol requires to send an init message, it should be implemented
here. You may or may not rely on methods from parent classes
(``connect/disconnect``, ``send/receive``).

For instance, the class ``KnxNet`` (connection class for KNX) implements ``UDP``
and overloads the ``receive()`` method to convert received bytes to a
``KnxFrame`` object.

.. code-block:: python

   def receive(self, timeout:float=1.0) -> object:
      data, address = super().receive(timeout)
      return KnxFrame(bytes=data, source=address)

We recommend that you do the same for your implementation and return a usable
frame object instead of a raw byte array.

Write frame, block and field classes
------------------------------------

BOF's core source code assumes that the network protocols transmit frames as
bytes arrays, which contain blocks, which contain fields. If they don't, you can
skip this part. Otherwise, your protocol implementation should include three
classes, inheriting from ``BOFFrame``, ``BOFBlock`` and ``BOFField``.

Most of the creation and parsing operation is handled directly by these BOF
classes, relying on what you wrote in a JSON file. Therefore:

- Block and frame require that you instantiate a specification object inheriting
  from ``BOFSpec`` in your subclass' constructor (``__init__``) prior to calling
  their init. For frames, you also need to specify the type of block to
  instantiate (BOF cannot guess :(). For instance::

    self._spec = KnxSpec()
    super().__init__(KnxBlock, **kwargs)
    self.update()

- All protocol-specific content must be added to your subclass, most probably by
  overloading ``BOFFrame``, ``BOFBlock`` and ``BOFField`` methods and
  properties. As an example, the setter for the attribute ``value`` in
  ``KnxField`` (inheriting from ``BOFField``) has been modified to handle and
  convert to bytes IPv4 addresses and KNX individual and group addresses::

    @value.setter
    def value(self, content) -> None:
        if isinstance(content, str):
            # Check if content is an IPv4 address (A.B.C.D):
            try:
                ip_address(content)
                content = byte.from_ipv4(content)
            except ValueError:
                # Check if content is a KNX address (X.Y.Z or X/Y/Z)
                knx_addr = byte.from_knx(content)
                content = knx_addr if knx_addr else content
        super(KnxField, self.__class__).value.fset(self, content)

.. note::

   The generic part of BOF's frames implementation has been written
   according to two protocol implementation (KNX and OPCUA). There may be
   some improvement to make (adding parts that are currently written
   directly to implementation in the core or removing parts that are not
   generic enough) and we count on you to let us know (or make the change
   yourself)!
