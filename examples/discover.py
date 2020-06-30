from sys import path, argv
path.append('../')

from bof import knx, BOFNetworkError

if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
else:
    knxnet = knx.KnxNet()
    try:
        knxnet.connect(argv[1], 3671)
        frame = knx.KnxFrame(type="DESCRIPTION REQUEST")
        print(frame)
        knxnet.send(frame)
        response = knxnet.receive()
        print(response)
    except BOFNetworkError as bne:
        print(str(bne))
    finally:
        knxnet.disconnect()
