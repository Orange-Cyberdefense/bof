"""
ToolBOF
-------

A simple script utility to run a set of ready-to-use features to interact with
industrial devices.

The functions called are in folder `tools`, each one can be used standalone as
well. Available:
- Discover (``tools/discover.py``): Network discovery using several industrial
  protocols.
"""

from sys import argv
from textwrap import wrap
from tools import discover

#-----------------------------------------------------------------------------#
# Constants                                                                   #
#-----------------------------------------------------------------------------#

# Available arguments
DISCOVER = "discover"
DISCOVER_HELP = "Discovery function"

AVAILABLE = [DISCOVER]
HELP = "BOF contains a set of ready-to-use features to interact with " \
       "industrial devices."

LINE_WIDTH = 79

def toolbof_help():
    print(("{:-^"+str(LINE_WIDTH)+"}").format("-"))
    for l in wrap(HELP, width=LINE_WIDTH):
        print(l)
    print(("{:-^"+str(LINE_WIDTH)+"}").format("-"))
    print("{0}: {1}".format(DISCOVER, discover.HELP))

#-----------------------------------------------------------------------------#
# Discover                                                                    #
#-----------------------------------------------------------------------------#
    
if len(argv) >= 2 and argv[1].lower() == DISCOVER.lower():
    discover.run(argv[1:])
else:
    print("ERROR: Invalid argument. Available: {0}.".format(", ".join(AVAILABLE)))
    toolbof_help()
