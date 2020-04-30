from sys import path
path.append('../')

from bof import knx, BOFNetworkError

knxnet = knx.KnxNet()
try:
    knxnet.connect("224.0.23.12", 3671)
    frame = knx.KnxFrame()
    frame.header.service_identifier.value = b"\x02\x03"
    hpai = knx.KnxBlock(type="HPAI")
    frame.body.append(hpai)
    print(frame)
    knxnet.send(bytes(frame))
    response = knxnet.receive()
    print(response)
except BOFNetworkError as bne:
    print(str(bne))
finally:
    knxnet.disconnect()
