# BOF KNX example
# Search for devices via the KNXnet/IP multicast address.
# Usage: python search.py
#
# Function search() sends a SEARCH REQUEST (KNXnet/IP) to KNX multicast
# address (default is 224.0.23.12, for custom address: search(addr)).
# search() returns a list of KNXDevice objects.
#
# search() and KNXDevice implemented in bof/layers/knx/knx_feature.py

from sys import path
path.append('../../')
from bof.layers.knx import search

devices = search()
for device in devices:
    print(device)
