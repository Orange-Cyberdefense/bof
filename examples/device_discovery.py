from sys import path, argv
path.append('../')

from bof import knx, BOFNetworkError

if len(argv) < 2:
    print("Usage: python {0} IP_RANGE".format(argv[0]))
else:
    devices = knx.discover(argv[1])
    if isinstance(devices, knx.KnxDevice):
        print(devices)
    else:
        for device in devices:
            print(device)
