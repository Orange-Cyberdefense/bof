from sys import path
path.append('../')

from bof import knx, BOFNetworkError

knxnet = knx.KnxNet()
try:
    knxnet.connect("localhost", 13671)
    frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
    print(frame)
    knxnet.send(frame)
    response = knxnet.receive()
    print(response)
except BOFNetworkError as bne:
    print(str(bne))
finally:
    knxnet.disconnect()
