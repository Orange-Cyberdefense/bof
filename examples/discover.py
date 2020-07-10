from sys import path, argv
path.append('../')

from bof import knx, BOFNetworkError

if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
else:
    knxnet = knx.KnxNet()
    ip, port = argv[1], 3671
    try:
        knxnet.connect(ip, port)
        frame = knx.KnxFrame(type="DESCRIPTION REQUEST")
        # print(frame)
        knxnet.send(frame)
        response = knxnet.receive()
        print(response)
        device = knx.KnxDevice(response, ip_address=ip, port=port)
        print(device)
    except BOFNetworkError as bne:
        print(str(bne))
    finally:
        knxnet.disconnect()
