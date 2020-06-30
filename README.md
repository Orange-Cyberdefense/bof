BOF 
===

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

**Please note that targeting BMS systems can have a severe impact on buildings and
people and that BOF must be used carefully.**

Getting started
---------------

```
git clone https://github.com/Orange-Cyberdefense/bof.git
```

BOF is a Python 3.6+ library that should be imported in scripts.  It has no
installer yet so you need to refer to the `bof` subdirectory which contains the
library (inside the repository) in your project or to copy the folder to your
project's folder. Then, inside your code (or interactively):

```
import bof
```

Now you can start using BOF!

> The following code samples interact using the building management system
  protocol KNXnet/IP (the framework supports only this one for now).

### Discover devices on a network

> Not implemented yet

### Send and receive packets

```
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
```

### Craft your own packets!

```
from bof import knx

frame = knx.KnxFrame()
frame.header.service_identifier.value = b"\x02\x03"
hpai = knx.KnxBlock(type="HPAI")
frame.body.append(hpai)
print(frame)
```

Complete documentation
----------------------

The HTML user manual and source code documentation can be built from the
repository:
 
1. `$> cd docs && make html`
2. Navigate to `[path to repository]/docs/_build/html/index.html)`

Example scripts are in folder `examples`.

Contributing
------------

Contributors are welcome! BOF is still an ongoing project and so far, we focused
on the detailed implementation of the KNX specification. One can already do the
main basic operations, but there are many types of frames and features in the
KNX standard (without even mentioning the extensions) and not all of them have
been implemented yet. Furthermore, there will still be room for higher-level
functions that will make tests easier.  We also wrote BOF so that it can be
extended to other field protocols (industrial, building management, etc.), so
why not implement another one?

Here a few things to know beforehand:

* We like clean code and expect contributions to be PEP-8 compliant as much as
  possible (even though we don't test for it). New code should be readable
  easily and maintainable. And remember: if you need to use "and" while
  explaining what your function does, then you can probably split it.

* Please write Unit tests! They are in `tests/`. You can run all unit tests
  with: `python -m unittest discover -s tests`

Reporting issues
----------------

Report bugs, ask questions or request for missing documentation and new features
by submitting an issue with GitHub. For bugs, please describe your problem as
clearly as you can.