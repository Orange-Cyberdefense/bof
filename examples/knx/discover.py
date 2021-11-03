from sys import argv, path
path.append('../../')
from bof.layers.knx import discover

if len(argv) > 1:
    print(discover(argv[1]))
