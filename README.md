BOF 
===

BOF (Boiboite Opener Framework) is a testing framework for field protocols
implementations and devices. It is a Python 3.6+ library that provides means to
send, receive, create, parse and manipulate frames from supported protocols.

The library currently provides discovery and extended testing features for
**KNXnet/IP**, which is our focus, but it can be extended to other types of BMS
or industrial network protocols. It also provides passive discovery functions
for industrial networks relying on KNXnet/IP, LLDP and Profinet DCP.

**Please note that targeting industrial systems can have a severe impact on
people, industrial operations and buildings and that BOF must be used
carefully.**

[![GitHub license](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/Orange-Cyberdefense/bof/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/release/Orange-Cyberdefense/bof.svg)](https://gitHub.com/Orange-Cyberdefense/bof/releases/)

Install
-------

### From PyPI

```
pip install boiboite-opener-framework
```

https://pypi.org/project/boiboite-opener-framework/

### Manual install

```
git clone https://github.com/Orange-Cyberdefense/bof.git
```

Install requirements with:

```
pip install -r requirements.txt
```

Protocol implementations use [Scapy](https://scapy.readthedocs.io/en/latest/)'s format.

Getting started
---------------

BOF is a Python 3.6+ library that should be imported in scripts.

```python
import bof
from bof.layers import profinet, knx
from bof.layers.knx import KnxPacket
```

There are three ways to use BOF, not all of them are available depending on the
layer:

* **Automated**: Import or call directly higher-level functions from layers. No
    knowledge about the protocol required.

* **Standard**: Craft packets from layers to interact with remote devices. Basic
    knowledge about the protocol requred.

* **Playful**: Play with packets, misuse the protocol (we fuzz devices with it).
  The end user should have started digging into the protocol's specifications.

|              | Automated | Standard | Playful |
|--------------|-----------|----------|---------|
| KNX          | X         | X        | X       |
| LLDP         | X         |          |         |
| Modbus       |           | X        | X       |
| Profinet DCP | X         |          |         |


Now you can start using BOF!

TL;DR
-----

### Several ways yo discover devices on a network

* Passive discovery from the discovery module:

```python
from bof.modules.discovery import *

devices = passive_discovery(iface="eth0", verbose=True)
```

* Device discovery using a layer's high-level function

```python
from bof.layers.knx import search

devices = search()
for device in devices:
    print(device)
```

* Create and send your own discovery packet:

```
from bof.layers.knx import *

pkt = KNXPacket(type="search request")
responses = KNXnet.multicast(pkt, (KNX_MULTICAST_ADDR, KNX_PORT))
for response, _ in responses:
    print(KNXPacket(response))
```

### Send and receive packets

```python
from bof.layers.knx import KNXnet, KNXPacket, SID
from bof import BOFNetworkError

try:
    knxnet = KNXnet().connect("192.168.1.242", 3671)
    pkt = KNXPacket(type=SID.description_request,
                    ip_address=knxnet.source_address,
                    port=knxnet.source_port)
    pkt.show2()
    response, _ = knxnet.sr(pkt)
    response.show2()
except BOFNetworkError as bne:
    pass
finally:
    knxnet.disconnect()
```

### Craft your own packets

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
  that BOF won't stop you from messing with your packets.

### Interface with Scapy

BOF relies on Scapy for protocol implementations, with an additional layer that
translates BOF code to changes on Scapy packets and fields. Why? Because BOF may
slightly modify or override Scapy’s internal behavior.

You do not need to know how to use Scapy to use BOF, however if you do, you are
free to interact with the Scapy packet directly as well.

```python
packet = KNXPacket(type=connect_request)
packet.field1 = 1 # Applying additional BOF operations (ex: change types)
packet.scapy_pkt.field1 = 1 # Direct access to Scapy Packet object
```

Complete documentation
----------------------

[![made-with-sphinx-doc](https://img.shields.io/badge/Made%20with-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/)

Link to the documentation: https://bof.readthedocs.io

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
explains how to do it. Furthermore, there will still be room for higher-level
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
