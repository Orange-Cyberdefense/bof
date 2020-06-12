from sys import path
path.append('../')

from bof import knx, BOFNetworkError, byte

def connect_request(knxnet, connection_type):
    connectreq = knx.KnxFrame(type="CONNECT REQUEST")
    connectreq.body.connection_request_information.connection_type_code.value = knxspecs.connection_types[connection_type]
    connectreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    connectreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
    connectreq.body.data_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    connectreq.body.data_endpoint.port.value = byte.from_int(knxnet.source[1])
    if connection_type == "Tunneling Connection":
        connectreq.body.connection_request_information.append(knx.KnxField(name="link layer", size=1, value=b"\x02"))
        connectreq.body.connection_request_information.append(knx.KnxField(name="reserved", size=1, value=b"\x00"))
    print(connectreq)
    connectresp = knxnet.send_receive(connectreq)
    knxnet.channel = connectresp.body.communication_channel_id.value

def disconnect_request(knxnet):
    discoreq = knx.KnxFrame(type="DISCONNECT REQUEST")
    discoreq.body.communication_channel_id = knxnet.channel
    discoreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    discoreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
    knxnet.send(discoreq)

def read_property(knxnet, sequence_counter, object_type, property_id):
    request = knx.KnxFrame(type="CONFIGURATION REQUEST", cemi="PropRead.req")
    request.body.communication_channel_id.value = knxnet.channel
    request.body.sequence_counter.value = sequence_counter
    request.body.cemi.number_of_elements.value = 1
    request.body.cemi.object_type.value = knxspecs.object_types[object_type]
    request.body.cemi.object_instance.value = 1
    request.body.cemi.property_id.value = knxspecs.properties[object_type][property_id]
    print(request)
    try:
        response = knxnet.send_receive(request) # ACK
        while (1):
            response = knxnet.receive() # PropRead.con
            if response.sid == "CONFIGURATION REQUEST":
                print(response)
                # We tell the boiboite we received it
                ack = knx.KnxFrame(type="CONFIGURATION ACK")
                ack.body.communication_channel_id.value = knxnet.channel
                ack.body.sequence_counter.value = sequence_counter
                knxnet.send(ack)
    except BOFNetworkError:
        pass #Timeout

knxspecs = knx.KnxSpec()
knxnet = knx.KnxNet()
knxnet.connect("192.168.1.10", 3671)

# Gather device information
connect_request(knxnet, "Device Management Connection")
read_property(knxnet, 0, "IP PARAMETER OBJECTS", "PID_ADDITIONAL_INDIVIDUAL_ADDRESSES")
read_property(knxnet, 1, "DEVICE", "PID_MANUFACTURER_ID")
disconnect_request(knxnet)

# Establish tunneling connection to read and write objects
connect_request(knxnet, "Tunneling Connection")
# TODO
disconnect_request(knxnet)
