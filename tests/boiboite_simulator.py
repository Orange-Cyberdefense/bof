"""Boiboite simulator, just replies the appropriate response to a request."""

import socket
import sys

DescrReq = b"\x06\x10\x02\x03\x00\x0e\x08\x01" # missing ip and port :)
DescrResp = b"\x06\x10\x02\x04\x00\x44\x36\x01\x02\x00\xff\xff\x00\x00\x00\x00" \
            b"\x54\xff\xf4\x13\xe0\x00\x17\x0c\x00\x00\x54\xff\xf4\x13\x73\x70" \
            b"\x61\x63\x65\x4c\x59\x6e\x6b\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x02\x02\x01" \
            b"\x03\x01\x04\x01"

ConnectReq = b"\x06\x10\x02\x05\x00\x18\x08\x01" # Beginning only
ConnectResp = b"\x06\x10\x02\x06\x00\x12\x01\x00\x08\x01\xc0\xa8\x00\x0a\x0e\x57" \
              b"\x02\x03"

def do_boiboite_stuff(data):
    print(data)
    if data.startswith(DescrReq):
        print("sending back DescrResp")
        return DescrResp
    if data.startswith(ConnectReq):
        print("sending back ConnectResp")
        return ConnectResp
    # Else echo
    return data

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 13671)
sock.bind(server_address)

while True:
    data, address = sock.recvfrom(4096)
    if data:
        sock.sendto(do_boiboite_stuff(data), address)
