from sys import path
path.append('../')

from bof import BOFNetworkError, knx, byte

"""Mini fuzzer for cEMI blocks in CONFIGURATION REQUEST frames."""

def connect(ip:str, port:int) -> (knx.KnxNet, int):
    """Set item required for connection (source ip and port), saves connection
    information returned by the KNXnet/IP server (channel).
    [ sends: CONNECT REQUEST | expects: CONNECT RESPONSE ]
    """
    knxnet = knx.KnxNet()
    knxnet.connect(ip, port)
    connectreq = knx.KnxFrame(type="CONNECT REQUEST")
    connectreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    connectreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
    connectreq.body.data_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    connectreq.body.data_endpoint.port.value = byte.from_int(knxnet.source[1])
    connectresp = knxnet.send_receive(connectreq)
    CHANNEL = connectresp.body.communication_channel_id.value
    return knxnet, channel

def disconnect(knxnet:knx.KnxNet, channel:int) -> None:
    """Disconnect from the KNXnet/IP server on given channel.
    [ sends: DISCONNECT REQUEST | expects: DISCONNECT RESPONSE ]
    """
    discoreq = knx.KnxFrame(type="DISCONNECT REQUEST")
    discoreq.body.communication_channel_id = channel
    discoreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    discoreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
    # print(discoreq)
    response = knxnet.send_receive(discoreq)
    # print(response)

knxnet, channel = connect("192.168.1.10", 3671)
# TODO, don't forget ACKs
disconnect(knxnet, channel)

# Note for paper:
# 1. Establish connection, save channel
# 2. Generate test frame inputs
# 3. Mutate targeted fields, save mutation location (field), value and type
# 4. Send mutation
# 5. Wait for CONFIGURATION ACK, if no such frame: DROP
# 6. How to detect errors? ---------- TODO
# 7. Disconnect at the end of the tests
