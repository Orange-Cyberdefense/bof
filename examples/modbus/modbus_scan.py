"""
    BOF usage example using Modbus.
    This script is a basic Modbus TCP scanner tool, able to scan an IP or range
    of IP for Modbus TCP devices, then enumerate their available functions and
    UIDs.

    Examples::

        python modbus_scan.py 192.168.56.102
        python modbus_scan.py -a 192.168.56.0/24
"""

import argparse
import ipaddress
import scapy.contrib.modbus as scapy_modbus
from socket import socket, AF_INET, SOCK_STREAM
from sys import path
path.append('../../')
from bof import ModbusNet, MODBUS_FUNCTIONS_CODES, ModbusPacket, MODBUS_TYPES


def tcp_scan(target, port=502):
    target_addresses = [str(ip) for ip in ipaddress.IPv4Network(target)]
    open_tcp = []
    for address in target_addresses:
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(0.1)
        conn = s.connect_ex((address, port))
        if (conn == 0):
            open_tcp.append(address)
        s.close()
    return open_tcp


def get_modbus_functions(modbus_server, modbus_port=502, unitId=0):
    modbus_net = ModbusNet()
    modbus_net.connect(modbus_server, modbus_port)
    supported_functions = []
    for code in MODBUS_FUNCTIONS_CODES:
        modbus_req = ModbusPacket(type=MODBUS_TYPES.REQUEST, function=code, unitId=unitId)
        modbus_resp, _ = modbus_net.sr(modbus_req)

        if isinstance(modbus_resp.payload, tuple(scapy_modbus._modbus_error_classes.values())):
            if not (modbus_resp.funcCode > 127 and \
                    ((hasattr(modbus_resp, 'exceptCode') and modbus_resp.exceptCode == 0x01) or
                     (hasattr(modbus_resp,
                              'exceptionCode') and modbus_resp.exceptionCode == 0x01))):
                supported_functions.append(code)
    return supported_functions


parser = argparse.ArgumentParser()
parser.add_argument("target", help="IP address/CIDR to scan", type=str)
parser.add_argument("port", help="Modbus port to check", nargs='?', type=int, default=502)
parser.add_argument("-f", "--functions", help="bruteforces Modbus Function Codes",
                    action="store_true")
parser.add_argument("-u", "--uids", help="bruteforces Modbus UIDs (not implemented yet)",
                    action="store_true")
parser.add_argument("-a", "--all", help="add all scan options (equivalent to -u -f)",
                    action="store_true")
args = parser.parse_args()

modbus_target = args.target
modbus_port = args.port
found_modbus = []
found_functions = {}

print("[*] Scanning {0} for Modbus TCP devices (port {1})".format(modbus_target, modbus_port))
found_modbus = tcp_scan(modbus_target, modbus_port)

if found_modbus and (args.functions or args.all):
    for modbus_server in found_modbus:
        found_functions[modbus_server] = get_modbus_functions(modbus_server, modbus_port)

print("[*] Found {0} Modbus TCP devices :".format(len(found_modbus)))
for modbus_server in found_modbus:
    print("")
    print("     Device address : {0}".format(modbus_server))
    if (modbus_server in found_functions.keys()):
        print("     Available Modbus functions :")
        for function in found_functions[modbus_server]:
            print(
                "         - {0} (code {1})".format(MODBUS_FUNCTIONS_CODES[function], hex(function)))
