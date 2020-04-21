from sys import path
path.append('../')

from bof import knx, BOFNetworkError

knxnet = knx.KnxNet()
try:
    knxnet.connect("localhost", 13671)
except BOFNetworkError as bne:
    print(str(bne))
frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
knxnet.send(bytes(frame))
response = knxnet.receive()
print(response)
knxnet.disconnect()
