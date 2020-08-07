from sys import path, argv
path.append('../')

from bof import knx, BOFNetworkError

def update_source(knxnet, field):
    field.ip_address.value = knxnet.source_address
    field.port.value = knxnet.source_port

def tunnel_connect(knxnet):
    tunnel_connect_request = knx.KnxFrame(type="CONNECT_REQUEST",
                                          connection="TUNNELING CONNECTION")
    update_source(knxnet, tunnel_connect_request.body.control_endpoint)
    update_source(knxnet, tunnel_connect_request.body.data_endpoint)
    tunnel_connect_response = knxnet.send_receive(tunnel_connect_request)
    return tunnel_connect_response.body.communication_channel_id.value

def tunnel_disconnect(knxnet, channel):
    tunnel_disconnect_request = knx.KnxFrame(type="DISCONNECT_REQUEST")
    tunnel_disconnect_request.body.communication_channel_id.value = channel
    update_source(knxnet, tunnel_disconnect_request.body.control_endpoint)
    tunnel_disconnect_response = knxnet.send_receive(tunnel_disconnect_request)

def group_write(knxnet, channel, kga, value):
    """Write ``value`` to knx group address ``kga`` on ``knxnet``"""
    request = knx.KnxFrame(type="TUNNELING REQUEST", cemi="L_Data.req")
    request.body.cemi.cemi_data.l_data_req.frame_type.value = 1
    request.body.cemi.cemi_data.l_data_req.repeat.value = 1
    request.body.cemi.cemi_data.l_data_req.broadcast_type.value = 1
    request.body.cemi.cemi_data.l_data_req.address_type.value = 1
    request.body.cemi.cemi_data.l_data_req.hop_count.value = 6
    request.body.cemi.cemi_data.l_data_req.source_address.value = b"\xff\xff" # TODO: 15.15.255
    request.body.cemi.cemi_data.l_data_req.destination_address.value = b"\x09\x01" # TODO: 15.15.255
    request.body.cemi.cemi_data.l_data_req.service.value = 2
    request.body.cemi.cemi_data.l_data_req.data.value = value
    received_ack = knxnet.send_receive(request)
    print(received_ack)
    response = knxnet.receive()
    print(response.cemi)
    if response.sid == "TUNNELING REQUEST":
        ack_to_send = knx.KnxFrame(type="TUNNELING ACK")
        ack_to_send.body.communication_channel_id.value = channel
        knxnet.send(ack_to_send)
    print(response)

if len(argv) < 4:
    print("Usage: {0} IP_ADDRESS KNX_GROUPADDRESS VALUE".format(argv[0]))
    exit(-1)

try:
    knxnet = knx.KnxNet()
    knxnet.connect(argv[1])
    channel = tunnel_connect(knxnet)
    group_write(knxnet, channel, argv[2], int(argv[3]))
    tunnel_disconnect(knxnet, channel)
except BOFNetworkError as bne:
    print(bne)
finally:
    knxnet.disconnect()
