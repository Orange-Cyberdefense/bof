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

LOG_FILENAME = "fuzzer_{0}.log".format(datetime.now().strftime("%y%m%d-%H%M%S"))

def WRITE(message:str) -> None:
    """Write message to any output we want."""
    LOG_FD.write(message)
    LOG_FD.write("\n")
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
        conn_req.scapy_pkt.control_endpoint.ip_address, conn_req.scapy_pkt.control_endpoint.port = knxnet.source
        conn_req.scapy_pkt.data_endpoint.ip_address, conn_req.scapy_pkt.data_endpoint.port = knxnet.source
        response, _ = knxnet.sr(conn_req)
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
        disco_req.ip_address, disco_req.port = knxnet.source
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
    fields = [x.name for x,y in packet._field_generator(packet.scapy_pkt.cemi) if x.name
              not in exclude_list]
    while 1:
        field, old_value, parent = packet._get_field(choice(fields))
        new_value = field.randval()
        packet[field.name] = new_value
        yield packet, "<{0}: {1}>".format(field.name, new_value)
        packet[field.name] = old_value
        # sleep(0.2)

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
        conf_ack = KNXPacket(type=SID.configuration_ack)
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
                try:
                    print("{0} requests sent, {1} event(s)... (Ctrl+C to stop)".format(total,triggers),
                          end="\r")
                    ack, _ = knxnet.sr(packet)
                    # If OK, device replies with an ACK frame we want to check
                    if ack.sid == SID.configuration_ack and not ack.status == 0x00:
                        WRITE("\n!!! Error in acknowledgement ({0})".format(ack))
                        WRITE("{0} ({1})".format(field, packet))
                        triggers += 1
                        disconnect(knxnet, channel)
                        break
                    # Then with a configuration request we have to reply to
                    conf, _ = knxnet.receive()
                    if conf.sid == SID.configuration_request:
                        conf_ack.communication_channel_id = channel
                        conf_ack.sequence_counter = sequence_counter
                        knxnet.send(conf_ack)
                    sequence_counter = sequence_counter + 1 if sequence_counter < 255 else 0
                    total += 1
                except BOFNetworkError: # Automatically disconnected.
                    WRITE("\n!!! Timeout")
                    WRITE("{0} ({1})".format(field, packet))
                    triggers += 1
                    break
    except KeyboardInterrupt:
        print("\nCancelled.")
    finally:
        disconnect(knxnet, channel)
        WRITE("*** ENDED with {0} triggers ({1} total requests sent). ***".format(triggers, total))
        LOG_FD.close()

#-----------------------------------------------------------------------------#
# RUN                                                                         #
#-----------------------------------------------------------------------------#

if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
    quit()

# Open log file
LOG_FD = open(LOG_FILENAME, "w+")
# Create the base frame to mutate during fuzzing
base_pkt = KNXPacket(type=SID.configuration_request, cemi=CEMI.m_propread_req)
base_pkt.number_of_elements = 1
base_pkt.show2()

# Run fuzzer
fuzz(argv[1], random_bytes, base_pkt)
