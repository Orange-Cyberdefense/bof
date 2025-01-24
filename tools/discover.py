from sys import path, argv
from argparse import ArgumentParser
from netifaces import ifaddresses
from ipaddress import ip_address
from time import sleep
# BOF
try:
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
    "they cannot \ninterpret, please only use broadcast and targeted modes on " \
    "test environments."

HELP = "Network discovery using several network protocols."

OPTIONS = (
    ("-L", "--light", "discover via sniffing and multicast (default)", False, None),    
    ("-B", "--broadcast", "discover via broadcast (only UDP)", False, None),
    ("-T", "--target", "target a device by IP", None, "ipaddress"),
    ("-i", "--iface", "specify interface name (default: eth0)", IFACE, "iface"),
    ("-t", "--timeout", "time to wait for sniffing (light)", TIMEOUT, "seconds")
)

#-----------------------------------------------------------------------------#
# Light                                                                       #
#-----------------------------------------------------------------------------#

def start_passive(iface):
    """Start passive sniffing (async)."""
    lldp_sniffer = lldp.start_listening(iface)
    return lldp_sniffer

def end_passive(lldp_sniffer):
    """Stop async sniffing and return results as a list of devices."""
    devices = lldp.stop_listening(lldp_sniffer)
    return [lldp.LLDPDevice(d) for d in devices]

def light(iface: str = IFACE, timeout: int = TIMEOUT):
    """Discover devices on a network using multicast and listening.

    Currently supported:
    - LLDP (passive listening, layer 2)
    - Profinet DCP (multicast, layer 2)
    - KNX (multicast, layer 3).
    """
    devices = []
    lldp_sniffer = start_passive(iface)
    try:
        devices += profinet.send_identify_request(iface, profinet.MULTICAST_MAC)
        devices += knx.search(knx.MULTICAST_ADDR, knx.PORT)
        sleep(timeout)
    except KeyboardInterrupt:
        print("Terminating, please wait.")
    devices += end_passive(lldp_sniffer)
    # Display results
    for device in devices:
        print(device)

#-----------------------------------------------------------------------------#
# Broadcast                                                                   #
#-----------------------------------------------------------------------------#
    
def broadcast(iface: str = IFACE):
    """Discover devices on a network by broadcasting UDP requests.

    Currently supported:
    - TODO
    """
    print(WARNING)
    if input("Do you want to continue? [y/N]: ") not in ("Y", "y"):
        return
    print("Gooo")

#-----------------------------------------------------------------------------#
# Targeted                                                                    #
#-----------------------------------------------------------------------------#
    
def targeted(iface: str = IFACE, target: str = None):
    """Discover a given device on the network with direct (unicast) requests.

    Currently supported:
    - TODO
    """
    print(WARNING)
    if input("Do you want to continue? [y/N]: ") not in ("Y", "y"):
        return
    print("Gooo")
    
#-----------------------------------------------------------------------------#
# Run                                                                         #
#-----------------------------------------------------------------------------#

def set_options():
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

def dispatch(args):
    opt = set_options()
    try:
        ifaddresses(opt.iface)
        if opt.broadcast:
            broadcast(opt.iface)
        elif opt.target:
            targeted(ip_address(opt.target))
        else:
            light(opt.iface, opt.timeout)
    except ValueError as ve:
        print("ERROR:", str(ve))
        exit (-1)

# If run standalone (can alse be called with bof.py discover)
if __name__ == "__main__":
    dispatch(argv)
