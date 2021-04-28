# BOF usage example using KNXnet/IP
# THis script is a basic fuzzer focussing on "cEMI", which are set of fields
# within a packet that will be transmitted to the KNX bus.
# Usage: python cemi_fuzzer.py IP_ADDRESS

from sys import path, argv
from datetime import datetime
from random import choice, getrandbits
from time import sleep
path.append('../../')

from bof.layers.knx import *
from bof import BOFNetworkError

#-----------------------------------------------------------------------------#
# REPORTING STUFF                                                             #
#-----------------------------------------------------------------------------#

def WRITE(message:str) -> None:
    """Write message to any output we want."""
    print(message)

#-----------------------------------------------------------------------------#
# CONNECTION MANAGEMENT                                                       #
#-----------------------------------------------------------------------------#

def connect(ip:str, port:int) -> (KNXnet, int):
    """Establish the connection with device and saves useful data in responses.
    Returns the connection object and the channel used by the device.
    """
    knxnet = KNXnet()
    channel = 0
    try:
        knxnet.connect(ip, port)
        conn_req = KNXPacket(type=SID.connect_request, connection_type=0x03)
        conn_req.control_endpoint.ip_address, conn_req.control_endpoint.port = knxnet.source
        conn_req.data_endpoint.ip_address, conn_req.data_endpoint.port = knxnet.source
        # TMP HACK ############################################################
        degueulasse = bytearray(bytes(conn_req)[:24])
        degueulasse[5:6] = b"\x18" # Manually change lengths
        degueulasse[22:23] = b"\x02"
        # END TMP HACK ########################################################
        response, _ = knxnet.sr(degueulasse)
        if response.sid == SID.connect_response and response.status == 0x00:
            channel = response.communication_channel_id
    except BOFNetworkError as bne:
        print(bne)
        return None, 0
    return knxnet, channel

def disconnect(knxnet:KNXnet, channel:int) -> None:
    """Disconnect from the device on given channel."""
    if knxnet:
        disco_req = KNXPacket(type=SID.disconnect_request, 
                              communication_channel_id = channel)
        disco_req.control_endpoint.ip_address, disco_req.control_endpoint.port = knxnet.source
        knxnet.send(disco_req)
        knxnet.disconnect()

#-----------------------------------------------------------------------------#
# GENERATORS                                                                  #
#-----------------------------------------------------------------------------#

def random_bytes(packet:KNXPacket) -> (KNXPacket, str):
    """Yields a KNXPacket with cEMI fields replaced with random values.
    We only change one field at a time.
    """
    exclude_list = ["cemi_data", "message_code", "data"]
    fields = [x.name for x,y in packet._field_generator(packet.cemi) if x.name
              not in exclude_list]
    while 1:
        field, old_value, parent = packet._get_field(choice(fields))
        new_value = field.randval()
        packet[field.name] = new_value
        yield packet, "<{0}: {1}>".format(field.name, new_value)
        packet[field.name] = old_value
        sleep(0.2) # TMP #####################################################

#-----------------------------------------------------------------------------#
# FUZZER                                                                      #
#-----------------------------------------------------------------------------#

def fuzz(ip:str, generator:object, base_pkt:KNXPacket) -> None:
    """Fuzz ``ip`` using ``generator`` to mutate ``base_pkt``.
    Runs in an infinite loop, used to disconnect and reconnect everytime one
    of the event we expect is triggered.
    """
    try:
        # INIT
        triggers = 0
        total = 0
        WRITE("*** START: {0} ***".format(datetime.now().strftime("%y-%m-%d-%H:%M:%S")))
        while 1:
            # SET OR RESET CONNECTION
            knxnet, channel = connect(ip, 3671)
            if not knxnet:
                break
            base_pkt.communication_channel_id = channel
            sequence_counter = 0
            # START SENDING PACKETS
            for packet, field in generator(base_pkt):
                packet.sequence_counter = sequence_counter
                WRITE("{0} ({1})".format(field, packet))
                try:
                    ack, _ = knxnet.sr(packet)
                    # If OK, device replies with an ACK frame we want to check
                    if not ack.status == 0x00:
                        WRITE("!!! Error in acknoledgement ({0})".format(ack))
                        triggers += 1
                        disconnect(knxnet, channel)
                        break
                    # Then with a configuration request we have to reply to
                    conf, _ = knxnet.receive()
                    if conf.sid == SID.configuration_request:
                        ack = KNXPacket(type=SID.configuration_ack,
                                        communication_channel_id=channel,
                                        sequence_counter=channel)
                        knxnet.send(ack)
                    sequence_counter += 1
                    total += 1
                except BOFNetworkError:
                    WRITE("!!! Timeout")
                    triggers += 1
                    # disconnect(knxnet, channel)
                    break
    except KeyboardInterrupt:
        print("Cancelled.")
    finally:
        disconnect(knxnet, channel)
        WRITE("*** ENDED with {0} triggers ({1} total requests sent). ***".format(triggers, total))

#-----------------------------------------------------------------------------#
# RUN                                                                         #
#-----------------------------------------------------------------------------#

if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
    quit()

# Create the base frame to mutate during fuzzing
base_pkt = KNXPacket(type=SID.configuration_request, cemi=CEMI.propread_req)
base_pkt.number_of_elements = 1
base_pkt.show2()

# Run fuzzer
fuzz(argv[1], random_bytes, base_pkt)
