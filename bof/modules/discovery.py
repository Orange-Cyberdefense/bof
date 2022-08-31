"""
Module: Discovery
-----------------

Functions for passive and active discovery of industrial devices on a network.
"""

from time import sleep
# Internal
from .. import DEFAULT_IFACE
from ..layers import knx, lldp, profinet

###############################################################################
# Passive discovery                                                           #
###############################################################################

def lldp_discovery(iface: str=DEFAULT_IFACE,
                   timeout: int=lldp.DEFAULT_TIMEOUT) -> list:
    """Search for devices on an network by listening to LLDP requests.
    
    Converts back asynchronous to synchronous with sleep (silly I know).  If you
    want to keep asynchrone, call directly ``start_listening`` and
    ``stop_listening`` in your code.

    Implementation in LLDP layer.
    """
    return lldp.listen_sync(iface, timeout)

def profinet_discovery(iface: str=DEFAULT_IFACE,
                       mac_addr: str=profinet.MULTICAST_MAC) -> list:
    """Search for devices on an network using multicast Profinet DCP requests.

    Implementation in Profinet layer.
    """
    return profinet.send_identify_request(iface, mac_addr)

def knx_discovery(ip: str=knx.MULTICAST_ADDR, port=knx.PORT, **kwargs):
    """Search for KNX devices on an network using multicast.

    Implementation in KNX layer.
    """
    return knx.search(ip, port)

def passive_discovery(iface: str=DEFAULT_IFACE,
                      pndcp_multicast: str=profinet.MULTICAST_MAC,
                      knx_multicast: str=knx.MULTICAST_ADDR,
                      verbose: bool=False):
    """Discover devices on an industrial network using passive methods.

    Requests are sent to protocols' multicast addresses or via broadcast.
    Currently, LLDP and KNX are supported.

    :param lldp_multicast: Multicast MAC address for LLDP requests.
    :param knx_multicast: Multicast IP address for KNXnet/IP requests.
    """
    vprint = lambda msg: print("[BOF] {0}.".format(msg)) if verbose else None
    multicast_protocols = {
        # Protocol name: [Discovery function, Multicast address]
        "Profinet": [profinet_discovery, pndcp_multicast],
        "KNX": [knx_discovery, knx_multicast]
    }
    total_devices = []
    # Start async sniffing
    vprint("Listening to LLDP requests...")
    lldp_sniffer = lldp.start_listening(iface)
    # Multicast requests send and receive
    for protocol, proto_args in multicast_protocols.items():
        discovery_fct, multicast_addr = proto_args
        vprint("Sending {0} request to {1}".format(protocol, multicast_addr))
        devices = discovery_fct(mac_addr=multicast_addr, iface=iface)
        nb = len(devices)
        vprint("{0} {1} {2} found".format(nb if nb else "No", protocol,
                                          "device" if nb <= 1 else "devices"))
        total_devices += devices
    # For now we need to wait a little longer to make sure we sniff something
    vprint("Still waiting for LLDP requests...")
    sleep(lldp.LLDP_DEFAULT_TIMEOUT - profinet.DEFAULT_TIMEOUT)
    # Stop async sniffing
    devices = lldp.stop_listening(lldp_sniffer)
    nb = len(devices)
    vprint("{0} {1} {2} found".format(nb if nb else "No", "LLDP",
                                      "device" if nb <= 1 else "devices"))
    total_devices += [lldp.LLDPDevice(device) for device in devices]
    for device in total_devices:
        vprint(device)
    return total_devices
