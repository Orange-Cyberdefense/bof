from sys import path, argv
from argparse import ArgumentParser
from netifaces import ifaddresses
from ipaddress import ip_address
from time import sleep
# BOF
try:
    from bof import BOFNetworkError
    from bof.layers import knx
    from bof.layers import profinet
    from bof.layers import lldp
except ImportError:
    path.append('../')
    from bof.layers import knx
    from bof.layers import profinet
    from bof.layers import lldp

#-----------------------------------------------------------------------------#
# Constants                                                                   #
#-----------------------------------------------------------------------------#

IFACE = "eth0" # Change with -i
TIMEOUT = 30 # Change with -t

WARNING = " /!\\ WARNING: Industrial devices may crash when receiving requests " \
    "they cannot \ninterpret, please only use broadcast and unicast modes on " \
    "test environments."

HELP = "Network discovery using several network protocols."

OPTIONS = (
    ("-L", "--light", "discover using passive and multicast (default)", False, None),
    ("-P", "--passive", "listen to the network without sending requests", False, None),    
    ("-M", "--multicast", "only send multicast requests (UDP only)", False, None),    
    ("-B", "--broadcast", "only send broadcast trquests (UDP only)", False, None),
    ("-T", "--target", "discover a specific target by connecting to it (TCP and UDP)",
     False, "target"),
    # ("-c", "--categories", "protocol categories to use (default: all)",
    #  "all", "categories"),
    ("-i", "--iface", "specify interface name (default: eth0)", IFACE, "iface"),
    ("-t", "--timeout", "time to wait for sniffing (light)", TIMEOUT, "seconds"),
    ("-v", "--verbose", "print more details about the process", False, None),
    ("-f", "--force", "do not print warning messages before dangerous tests", False, None)
)

VERBOSE = False
FORCE = False

def vprint(msg: str) -> None:
    if VERBOSE: print("[BOF] {0}".format(msg))

def warn() -> None:
    if not FORCE:
        print(WARNING)
        if input("Do you want to continue? [y/N]: ") not in ("Y", "y"):
            return False
    return True
    
#-----------------------------------------------------------------------------#
# Passive                                                                       #
#-----------------------------------------------------------------------------#

def start_passive(iface: str) -> object:
    """Start passive sniffing (async).

    Protocols: LLDP (L2).
    """
    vprint("Starting network listener.")
    lldp_sniffer = lldp.start_listening(iface)
    return lldp_sniffer

def end_passive(lldp_sniffer: object) -> list:
    """Stop async sniffing and return results as a list of devices.

    Protocols: LLDP (L2).
    """
    devices = lldp.stop_listening(lldp_sniffer)
    vprint("Stopping network listener.")
    return [lldp.LLDPDevice(d) for d in devices]

def passive(iface: str) -> list:
    """Listen to the network without sending requests.

    Protocols: LLDP (L2).
    """
    lldp_sniffer = start_passive(iface)
    try:
        sleep(timeout)
    except KeyboardInterrupt:
        print("Terminating, please wait.")
    return end_passive(lldp_sniffer)

#-----------------------------------------------------------------------------#
# Light                                                                       #
#-----------------------------------------------------------------------------#

def multicast(iface: str) -> list:
    """Discover devices using protocols that support multicast (L2, UDP).

    Protocols: Profinet DCP (L2), KNXnet/IP (UDP).
    """
    pdcp_list, knx_list = [], []
    vprint("Profinet DCP discovery (multicast).")
    pdcp_list = profinet.send_identify_request(iface, profinet.MULTICAST_MAC)
    vprint("Found {0} Profinet DCP devices.".format(len(pdcp_list)))
    vprint("KNXnet/IP discovery (multicast).")
    knx_list = knx.search(knx.MULTICAST_ADDR, knx.PORT)
    vprint("Found {0} KNXnet/IP devices.".format(len(knx_list)))
    return pdcp_list + knx_list

#-----------------------------------------------------------------------------#
# Light                                                                       #
#-----------------------------------------------------------------------------#

def light(iface: str = IFACE, timeout: int = TIMEOUT) -> list:
    """Discovery without sending direct requests to all devices.

    Modes: passive, multicast
    - LLDP (passive listening, layer 2)
    - Profinet DCP (multicast, layer 2)
    - KNX (multicast, layer 3).
    """
    devices = []
    lldp_sniffer = start_passive(iface)
    try:
        devices += multicast(iface)
        sleep(timeout)
    except KeyboardInterrupt:
        print("Terminating, please wait.")
    devices += end_passive(lldp_sniffer)
    return devices

#-----------------------------------------------------------------------------#
# Broadcast                                                                   #
#-----------------------------------------------------------------------------#
    
def broadcast(iface: str = IFACE) -> list:
    """Discover devices on a network by broadcasting UDP requests.

    Currently supported:
    - TODO
    """
    if not warn():
        return []
    vprint("TODO discovery (broadcast).")
    raise NotImplementedError("broadcast")
    return []

#-----------------------------------------------------------------------------#
# Targeted                                                                    #
#-----------------------------------------------------------------------------#
    
def targeted(target: str = None) -> list:
    """Discover a given device on the network with direct (unicast) requests.

    Currently supported:
    - KNXnet/IP
    """
    results = []
    if not warn():
        return results
    vprint("KNXnet/IP discovery on target {0}.".format(target))
    try:
        knx_dev = knx.discover(target) # Should return only one object
        results.append(knx_dev)
    except BOFNetworkError:
        vprint("No KNXnet/IP device found at {0}.".format(target))
    return results

#-----------------------------------------------------------------------------#
# Run                                                                         #
#-----------------------------------------------------------------------------#

def set_options() -> object:
    options = ArgumentParser(description=HELP, epilog=WARNING)
    options.add_argument("mode") # discover
    for opt in OPTIONS:
        if not opt[4]: # Options takes no argument (so no meta)
            options.add_argument(opt[0], opt[1], help=opt[2],
                                 action="store_true", default=opt[3])
        else:
            options.add_argument(opt[0], opt[1], help=opt[2],
                                 metavar=opt[4], default=opt[3])
    return options.parse_args()

def display(results: list) -> None:
    """Print the list of devices found using discover."""
    for result in results:
        print(result)

def run(args) -> None:
    """Run the discovery module according to the options provided."""
    global VERBOSE, FORCE
    opt = set_options()
    options = (opt.passive, opt.multicast, opt.broadcast, opt.target)
    VERBOSE = opt.verbose
    FORCE = opt.force
    results = []
    try:
        ifaddresses(opt.iface)
        if opt.passive:
            results += passive(opt.iface)
        if opt.multicast:
            results += multicast(opt.iface)
        if opt.broadcast:
            results += broadcast(opt.iface)
        if opt.target:
            results += targeted(ip_address(opt.target))
        if opt.light or all(value is False for value in options):
            results += light(opt.iface, opt.timeout)
    except ValueError as ve:
        print("[ERROR]", str(ve))
        exit (-1)
    display(results)
        
# If run standalone (can alse be called with bof.py discover)
if __name__ == "__main__":
    run(argv)
