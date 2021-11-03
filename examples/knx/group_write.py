from sys import argv, path
path.append('../../')
from bof.layers.knx import *

if len(argv) != 4:
    print("Usage: python group_write.py IP KNX_GROUP_ADDR VALUE")
    exit(-1)
    
group_write(argv[1], argv[2], argv[3])
