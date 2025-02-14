BOF 
===

**BOF (Boiboite Opener Framework) is a Python 3 framework to interact and test
systems using industrial network protocols.**

It provides tools for industrial networks and devices discovery and to conduct
cybersecurity-related tests on them. It can also be used as a library, as it
contains the means to send, receive, create, parse and manipulate packets for
supported protocols. This is particularly useful if you want to write fuzzers or
other offensive testing scripts.

**Please note that targeting industrial systems can have a severe impact on
people, industrial operations and buildings and that BOF must be used
carefully.**

BOF relies on [Scapy](https://github.com/secdev/scapy) for protocol
implementations, with extra seasoning for some protocols to enhance its intended
flavor (e.g. change field types on-the-fly in packets for fuzzing purposes).
See [Note on Scapy](#note-on-scapy) below for details.

[![GitHub license](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/Orange-Cyberdefense/bof/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/release/Orange-Cyberdefense/bof.svg)](https://gitHub.com/Orange-Cyberdefense/bof/releases/)

The following protocols are currently implemented:

|                  | Discovery | Basic interaction | Built-in attacks | Packet manipulation |
|------------------|-----------|-------------------|------------------|---------------------|
| **KNXnet/IP**    | X         | X                 | -                | X                   |
| **LLDP**         | X         | -                 | -                | -                   |
| **Modbus**       | X         | X                 | -                | X                   |
| **Profinet DCP** | X         | X                 | -                | -                   |

As their are multiple modes in BOF, not all protocols have the same capabilities
implemented. For some of them, only the basic code required for network
discovery is there. For others, the most common message types are implemented
and can be extensively messed with. Feel free to send PR if something you need
is missing.

> LLDP is only implemented for discovery as it is used by network devices,
  including industrial ones. There is no plan for extending the implementation
  of this protocol in BOF.

Contents:

* [TL;DR](#tldr)
* [Discover](#discover)
* [Exploit](#exploit)
* [Build (Use BOF as a library)](#build-use-bof-as-a-library)

**Please refer to [BOF's documentation](https://bof.readthedocs.io/en/latest/) for
the detailed user and developer manuals.**

TL;DR
-----

**Devices discovery on a network**:

```
python bof.py discover -i eth0 -v # Light mode (passive and multicast)
python bof.py discover -i eth0 -T 192.168.1.1 -v (direct requests to device)
```

> Note: Some options require administrator privileges.

See [Discover](#discover) for details.

**Run built-in attacks**:

```
TODO
```

See [Exploit](#exploit) for details.

**Create a script using BOF capabilities**:

```
from bof.layers.knx import *

pkt = KNXPacket(type="search request")
responses = KNXnet.multicast(pkt, (KNX_MULTICAST_ADDR, KNX_PORT))
for response, _ in responses:
    print(KNXPacket(response))
```

* See [Build](#build-use-bof-as-a-library) and [BOF's
  documentation](https://bof.readthedocs.io/en/latest/) for details.

Discover
--------

TODO

Attack
------

TODO

Build (Use BOF as a library)
----------------------------

### Install

<!-- PYPI PACKAGE NOT UP-TO-DATE, COMMENTED FOR NOW
#### From PyPI
```
pip install boiboite-opener-framework
```
https://pypi.org/project/boiboite-opener-framework/ 
### Manual install
-->

```
git clone https://github.com/Orange-Cyberdefense/bof.git
pip install -r requirements.txt
```

> Note: Protocol implementations use [Scapy](https://github.com/secdev/scapy)'s
  format. There are imported directly from the Scapy package, but from time to
  time they can be included in BOF's package, if the version used is not in
  Scapy's latest version (yet).

### Import in Python script

```python
import bof
from bof.layers import profinet, knx
from bof.layers.knx import KnxPacket
```

### Write code

Depending on the protocol implementation in BOF, the following capabilities are
provided or not (details in [BOF's
documentation](https://bof.readthedocs.io/en/latest/)):

* [High-level usage](#high-level-usage)
* [Craft and manipulate packets](#craft-and-manipulate-packets)
* [Mess with the protocol](#mess-with-the-protocol)

#### High-level usage

Use high-level functions to interact with devices using this protocol. No need
to know how the protocol works.

Available for: **All protocols**.

```python
from bof.layers.knx import search

devices = search()
for device in devices:
    print(device)
```

#### Craft and manipulate packets

Craft and manipulate packets in a defined protocol. Requires to know a few
things about their specifications.

Available for: **KNXnet/IP**, **Modbus**, **Profinet DCP**.

> Important note: So far, Scapy layer and/or BOF implementation are not
  comprehensive implementations of the specifications. This means that only a
  some message types are supported for each protocol. Their number vary
  depending on the protocol. The messages supported are usually the ones related
  to network discovery and the most common messages used to interact with
  devices.

```
from bof.layers.knx import *

pkt = KNXPacket(type="search request")
responses = KNXnet.multicast(pkt, (KNX_MULTICAST_ADDR, KNX_PORT))
for response, _ in responses:
    print(KNXPacket(response))
```

#### Mess with the protocol

Play with packets and misuse the protocol. This is particularly useful to write
fuzzers, as BOF allows setting values of the wrong type in fields when crafting
packets (Scapy alone does not support that). Requires to have had a closer look
at the protocol's specifications.

Available for: **KNXnet/IP**, **Modbus**

```python
from bof.layers.knx import KNXPacket, SID
from bof.layers.raw_scapy.knx import LcEMI

pkt = KNXPacket(type=SID.description_request)
pkt.ip_address = b"\x01\x01"
pkt.port = 99999 # Yes it's too large
pkt.append(LcEMI())
pkt.show2() # This may output something strange
```

> A recipient device will probably not respond to that, but at least you know
  that BOF won't stop you from doing stupid things.

Note on Scapy
-------------

BOF relies on Scapy for protocol implementations, with an additional layer that
translates BOF code to changes on Scapy packets and fields. Indeed, BOF slightly
modifies or override Scapy’s internal behavior for security-testing
purposes. How we do this and why we do this is explained in [BOF's
documentation](https://bof.readthedocs.io/en/latest/man/user.html#interface-with-scapy).

You do not need to know how to use Scapy to use BOF, however if you do, you are
free to interact with the Scapy packet directly as well.

```python
packet = KNXPacket(type=connect_request)
packet.field1 = 1 # Applying additional BOF operations (ex: change types)
packet.scapy_pkt.field1 = 1 # Direct access to Scapy Packet object
```

Documentation
-------------

[![made-with-sphinx-doc](https://img.shields.io/badge/Made%20with-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/)

Link to the documentation: **https://bof.readthedocs.io**

The HTML user manual and source code documentation can be built from the
repository:
 
1. `$> cd docs && make html`
2. Navigate to `[path to repository]/docs/_build/html/index.html`

Example scripts are in folder `examples`.

Contributing
------------

Contributors are welcome! BOF is still an ongoing project, which relies on
industrial network protocol implementations in Scapy format. You can first
contribute by contributing to Scapy and adding new protocols ("layers"). Or, you
can contribute by integrating a Scapy protocol to BOF. The documentation
explains how to do it. Furthermore, there will still be room for high-level
functions that will make tests easier or implement known attack against
protocols or protocol implementations.

Here a few things to know beforehand:

* We like clean code and expect contributions to be PEP-8 compliant as much as
  possible (even though we don't test for it). New code should be readable
  easily and maintainable. And remember: if you need to use "and" while
  explaining what your function does, then you can probably split it.

* Please write Unit tests and make sure existing ones still pass! They are in
  `tests/`. You can run all unit tests with: `python -m unittest discover -s
  tests`

Reporting issues
----------------

Report bugs, ask questions or request for missing documentation and new features
by submitting an issue with GitHub. For bugs, please describe your problem as
clearly as you can.
