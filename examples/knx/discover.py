path.append('../../')
from bof.layers.knx import search

devices = search()
for device in devices:
    print(device)
