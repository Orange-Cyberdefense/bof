from sys import path
path.append('../')

from bof import knx, BOFNetworkError

knxnet = knx.KnxNet()
try:
    knxnet.connect("192.168.1.10", 3671)
    frame = knx.KnxFrame(type="CONFIGURATION REQUEST", cemi="PropRead.req")
    print(frame)
    knxnet.send(frame)
    response = knxnet.receive()
    print(response)
except BOFNetworkError as bne:
    print(str(bne))
finally:
    knxnet.disconnect()
