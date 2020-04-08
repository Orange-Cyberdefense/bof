from sys import path
path.append('../')

from bof import knx, BOFNetworkError

knxnet = knx.KnxNet()
try:
    knxnet.connect("localhost", 13671, init=False)
except BOFNetworkError as bne:
    print(str(bne))

frame = knx.KnxFrame(sid="DESCRIPTION_REQUEST")
new_body = knx.KnxStructure.build_from_type("DIB_DEVICE_INFO", name="dib")

frame.header.service_identifier.value = b"\x02\x05" # Connect Request
frame.remove("control_endpoint")
frame.body.append(new_body)

knxnet.send(bytes(frame))
response = knxnet.receive()
if len(response):
    print(bytes(response.header.service_identifier))
knxnet.disconnect()
