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

**Please note that targeting industrial systems can have a severe impact on
buildings and people and that BOF must be used carefully.**

[![GitHub license](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/Orange-Cyberdefense/bof/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/release/Orange-Cyberdefense/bof.svg)](https://gitHub.com/Orange-Cyberdefense/bof/releases/)

Getting started
---------------

```
git clone https://github.com/Orange-Cyberdefense/bof.git
```

BOF is a Python 3.6+ library that should be imported in scripts.  It has no
installer yet so you need to refer to the `bof` subdirectory which contains the
library (inside the repository) in your project or to copy the folder to your
project's folder. Then, inside your code (or interactively), you can import the
library:

```python
import bof
```

Now you can start using BOF!

TL;DR
-----

> TODO

Complete documentation
----------------------

[![made-with-sphinx-doc](https://img.shields.io/badge/Made%20with-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/)

Link to the documentation: https://bof.readthedocs.io

The HTML user manual and source code documentation can be built from the
repository:
 
1. `$> cd docs && make html`
2. Navigate to `[path to repository]/docs/_build/html/index.html)`

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

* Please write Unit tests! They are in `tests/`. You can run all unit tests
  with: `python -m unittest discover -s tests`

Reporting issues
----------------

Report bugs, ask questions or request for missing documentation and new features
by submitting an issue with GitHub. For bugs, please describe your problem as
clearly as you can.
