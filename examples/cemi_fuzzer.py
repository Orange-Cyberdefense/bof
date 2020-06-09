from sys import path
path.append('../')

from random import getrandbits, randint, choice
from bof import BOFNetworkError, knx, byte

"""Mini fuzzer for cEMI blocks in CONFIGURATION REQUEST frames."""

def connect(ip:str, port:int) -> (knx.KnxNet, int):
    """Set item required for connection (source ip and port), saves connection
    information returned by the KNXnet/IP server (channel).
    [ sends: CONNECT REQUEST | expects: CONNECT RESPONSE ]
    """
    knxnet = knx.KnxNet()
    channel = 0
    knxnet.connect(ip, port)
    connectreq = knx.KnxFrame(type="CONNECT REQUEST")
    connectreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    connectreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
    connectreq.body.data_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    connectreq.body.data_endpoint.port.value = byte.from_int(knxnet.source[1])
    try:
        response = knxnet.send_receive(connectreq)
        if response.sid == "CONNECT RESPONSE" and response.body.status.value == b'\x00':
            channel = response.body.communication_channel_id.value
    except BOFNetworkError:
        print("Connection failed.")
        exit(-1)
    return knxnet, channel

def disconnect(knxnet:knx.KnxNet, channel:int) -> None:
    """Disconnect from the KNXnet/IP server on given channel.
    [ sends: DISCONNECT REQUEST | expects: DISCONNECT RESPONSE ]
    """
    discoreq = knx.KnxFrame(type="DISCONNECT REQUEST")
    discoreq.body.communication_channel_id.value = channel
    discoreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    discoreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
    knxnet.send(discoreq)

def save(event, request, data, response=None):
    """Save request and data mutated that triggered the behavior.
    Should be saved instead of printed :)
    """
    print("--- {0} with data {1}".format(event, data))
    print("--- Request: {0}".format(bytes(request)))
    if response:
        print(response)

def all_properties(propread_req:knx.KnxFrame) -> (knx.KnxFrame, tuple):
    """Yields one frame for each property existing in all property type
    written to the specification JSON file."""
    specs = knx.KnxSpec()
    propread_req.body.cemi.object_instance.value = 1
    for prop_type in specs.properties_types:
        propread_req.body.cemi.object_type.value = specs.properties_types[prop_type]["id"]
        for prop in specs.properties[prop_type]:
            propread_req.body.cemi.property_id.value = specs.properties[prop_type][prop]["id"]
            yield propread_req, (prop_type, prop)

def random_properties(propread_req:knx.KnxFrame) -> (knx.KnxFrame, str):
    """Yields a frame with properties replaced with random values a 
    random number of times."""
    fields_with_exclusion = [x for x in propread_req.body.cemi.fields if x.name != "message code"]
    for _ in range(randint(1, 10000)):
        field = choice(fields_with_exclusion)
        save = field.value
        field.value = bytes(map(getrandbits,(8,)*field.size))
        print(str(field))
        yield propread_req, str(field)
        field.value = save

def fuzz(generator, initial_frame):
    """Fuzz using a generator to mutate initial frame."""
    try:
        for propread_req, data in generator(initial_frame):
            knxnet, channel = connect("192.168.1.10", 3671)
            propread_req.body.communication_channel_id.value = channel
            try:
                knxnet.send(propread_req)
                ack = knxnet.receive()
                propread_con = knxnet.receive()
                if propread_con.sid == "CONFIGURATION REQUEST":
                    ack = knx.KnxFrame(type="CONFIGURATION ACK")
                    ack.body.communication_channel_id.value = channel
                    knxnet.send(ack)
            except BOFNetworkError:
                save("Timeout", propread_req, data)
            finally:
                disconnect(knxnet, channel)
    except KeyboardInterrupt:
        print("Cancelled.")
        disconnect(knxnet, channel)

propread = knx.KnxFrame(type="CONFIGURATION REQUEST", cemi="PropRead.req")
propread.body.cemi.number_of_elements.value = 1
fuzz(all_properties, propread)
fuzz(random_properties, propread)
