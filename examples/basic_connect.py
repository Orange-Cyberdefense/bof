from sys import path
path.append('../')

from bof import knx, BOFNetworkError

knxnet = knx.KnxNet()
try:
    knxnet.connect("localhost", 13671, init=False)
except BOFNetworkError as bne:
    print(str(bne))
frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
knxnet.send(bytes(frame))
response = knxnet.receive()
print(bytes(response.header.service_identifier))
# Should print b'\x02\x04' (DESCRIPTION RESPONSE)
print(bytes(response.body.device_hardware.friendly_name).decode('utf-8'))
# Should print the name of the device as a string
knxnet.disconnect()
