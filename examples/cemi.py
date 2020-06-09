from sys import path
path.append('../')

from bof import knx, BOFNetworkError, byte

knxnet = knx.KnxNet()
knxnet.connect("192.168.1.10", 3671)
connectreq = knx.KnxFrame(type="CONNECT REQUEST")
connectreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
connectreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
connectreq.body.data_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
connectreq.body.data_endpoint.port.value = byte.from_int(knxnet.source[1])
# print(connectreq)
connectresp = knxnet.send_receive(connectreq)
channel = connectresp.body.communication_channel_id.value

request = knx.KnxFrame(type="CONFIGURATION REQUEST", cemi="PropRead.req")
request.body.communication_channel_id.value = channel
request.body.cemi.number_of_elements.value = 1
request.body.cemi.object_type.value = 11
request.body.cemi.property_id.value = 53
print(request)
try:
    response = knxnet.send_receive(request) # ACK
    while (1):
        response = knxnet.receive() # PropRead.con
        if response.sid == "CONFIGURATION REQUEST":
            # TEST SUBFIELDS
            response.body.cemi.number_of_elements_start_index.value = b'\x10\x01'
            print(byte.bit_list_to_int(response.body.cemi.number_of_elements.value))
            print(response)
            # We tell the boiboite we received it
            ack = knx.KnxFrame(type="CONFIGURATION ACK")
            ack.body.communication_channel_id.value = channel
            # ack.body.communication_channel_id.value = 1 # Set as default so far
            knxnet.send(ack)
            # print(ack)
except BOFNetworkError:
    pass #Timeout
discoreq = knx.KnxFrame(type="DISCONNECT REQUEST")
discoreq.body.communication_channel_id = channel
discoreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
discoreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
# print(discoreq)
response = knxnet.send_receive(discoreq)
# print(response)
