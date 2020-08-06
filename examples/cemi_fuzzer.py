from sys import path, argv
path.append('../')

from datetime import datetime
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
    try:
        knxnet.connect(ip, port)
        connectreq = knx.KnxFrame(type="CONNECT REQUEST",
                                  connection="DEVICE MANAGEMENT CONNECTION")
        connectreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
        connectreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
        connectreq.body.data_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
        connectreq.body.data_endpoint.port.value = byte.from_int(knxnet.source[1])
        response = knxnet.send_receive(connectreq)
        if response.sid == "CONNECT RESPONSE" and response.body.status.value == b'\x00':
            channel = response.body.communication_channel_id.value
    except BOFNetworkError as bne:
        print(bne)
        return None, 0
    return knxnet, channel

def disconnect(knxnet:knx.KnxNet, channel:int) -> None:
    """Disconnect from the KNXnet/IP server on given channel.
    [ sends: DISCONNECT REQUEST | expects: DISCONNECT RESPONSE ]
    """
    if knxnet:
        discoreq = knx.KnxFrame(type="DISCONNECT REQUEST")
        discoreq.body.communication_channel_id.value = channel
        discoreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
        discoreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
        knxnet.send(discoreq)
        knxnet.disconnect()

def save(event, request, data, response=None):
    """Save request and data mutated that triggered the behavior.
    Should be saved instead of printed :)
    """
    with open("fuzzing_results.txt", "a") as fd:
        fd.write("\n")
        fd.write("--- {0} with data {1}".format(event, data))
        fd.write("--- Request: {0}".format(bytes(request)))
        if response:
            fd.write(response)
        print("X")

def all_properties(propread_req:knx.KnxFrame) -> (knx.KnxFrame, tuple):
    """Yields one frame for each property existing in all property type
    written to the specification JSON file."""
    specs = knx.KnxSpec()
    propread_req.body.cemi.object_instance.value = 1
    for prop_type in specs.object_types:
        propread_req.body.cemi.object_type.value = specs.object_types[prop_type]
        for prop in specs.properties[prop_type]:
            propread_req.body.cemi.property_id.value = specs.properties[prop_type][prop]
            yield propread_req, (prop_type, prop)

def random_properties(propread_req:knx.KnxFrame) -> (knx.KnxFrame, str):
    """Yields a frame with properties replaced with random values a 
    random number of times."""
    fields_with_exclusion = [x for x in propread_req.body.cemi.fields if x.name != "message code"]
    # for _ in range(randint(1, 10000)):
    while 1:
        field = choice(fields_with_exclusion)
        save = field.value
        field.value = bytes(map(getrandbits,(8,)*field.size))
        yield propread_req, str(field)
        field.value = save

def fuzz(ip, generator, initial_frame):
    """Fuzz using a generator to mutate initial frame."""
    try:
        triggers = 0
        total = 0
        with open("fuzzing_results.txt", "a") as fd:
            fd.write(datetime.now().strftime("%y-%m-%d-%H:%M:%S")+"\n")
        while 1: # Each trigger resets the loop.
            knxnet, channel = connect(ip, 3671)
            if not knxnet:
                break
            initial_frame.body.communication_channel_id.value = channel
            sequence_counter = 0
            for propread_req, data in generator(initial_frame):
                propread_req.body.sequence_counter.value = sequence_counter
                try:
                    knxnet.send(propread_req)
                    print(".", end='', flush=True)
                    received_ack = knxnet.receive()
                    if received_ack.body.status.value == b"\x00": # Code 00 is OK
                        propread_con = knxnet.receive()
                        if propread_con.sid == "CONFIGURATION REQUEST":
                            ack_to_send = knx.KnxFrame(type="CONFIGURATION ACK")
                            ack_to_send.body.communication_channel_id.value = channel
                            ack_to_send.body.sequence_counter.value = sequence_counter
                            knxnet.send(ack_to_send)
                    else:
                        save("Error in acknowledgement", propread_req, data, received_ack)
                        triggers += 1
                        disconnect(knxnet, channel)
                        break
                except BOFNetworkError:
                    save("Timeout", propread_req, data)
                    triggers += 1
                    disconnect(knxnet, channel)
                    break
                sequence_counter += 1
                total += 1
    except KeyboardInterrupt:
        print("Cancelled.")
    finally:
        disconnect(knxnet, channel)
        with open("fuzzing_results.txt", "a") as fd:
            fd.write("*** ENDED WITH {0} TRIGGERS (Total: {1}) ***\n".format(triggers, total))
            fd.write(datetime.now().strftime("%y-%m-%d-%H:%M:%S")+"\n")

if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
    quit()

propread = knx.KnxFrame(type="CONFIGURATION REQUEST", cemi="PropRead.req")
propread.body.cemi.cemi_data.propread_req.number_of_elements.value = 1
# fuzz(all_properties, propread)
fuzz(argv[1], random_properties, propread)
