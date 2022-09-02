"""
Using modules
=============

Modules are higher-level features provided by BOF. They can rely on one or
more layer, depending on what they do. Basically, each module is a collection
of functions to call in a script.

List of modules:

* **Discovery**: Functions to gather initial information on industrial devices
  on a network, using active and passive techniques. Rely on several protocols.
"""

from .discovery import *
