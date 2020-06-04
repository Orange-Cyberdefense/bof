from bof import knx, BOFNetworkError

knxnet = knx.KnxNet()
knxnet.connect("192.168.1.10", 3671)
knxnet.send_receive(knx.KnxFrame(type="CONNECT REQUEST"))
request = knx.KnxFrame(type="CONFIGURATION REQUEST", cemi="PropRead.req")
request.body.cemi.number_of_elements.value = 16
request.body.cemi.object_type.value = 11
request.body.object_instance.value = 1
request.body.cemi.property_id.value = 53
print(request)
response = knxnet.send_receive(request)
print(response)
try:
    while (1):
        response = knxnet.receive()
        print(response)
except BOFNetworkError:
    pass #Timeout
knxnet.send_receive(knx.KnxFrame(type="DISCONNECT REQUEST"))
