Discovery
=========

Overview
--------

This module constains high-level functions for device discovery on a network
using several protocols.

Targeted discovery
------------------

When discovering devices on an industrial network, the less we interact directly
with devices the better (otherwise we may break something). The
``targeted_discovery()`` function sends identify requests to protocol-specific
multicast addresses. Devices that subscribe to them are supposed to respond.

.. code-block:: python

   targeted_discovery(iface="eth0", verbose=True)

So far, here is what the function does:

* Listen to **LLDP** multicast address (switches and other network usually send
  LLDP packets with their description)
* Send a **Profinet DCP** identify request
* Send a **KNXnet/IP** search request

Other discovery functions
-------------------------

The following discovery functions are available independently:

:``lldp_discovery()``: Listen on the network for LLDP packets sent on LLDP's
		       multicast MAC address. This function is synchronous. For
		       the async version, call ``lldp.start_listening()`` and
		       ``lldp.stop_listening()``.
:``profinet_discovery()``: Send an identify request on Profinet DCP's multicast
			   MAC address.
:``knx_discovery()``: Send a search request on KNXnet/IP's multicast IP address.
			   
