# BOF usage example using KNXnet/IP
# This script will send a write request to a KNX group address.
# Usage: python group_write.py IP_ADDRESS GROUP_ADDRESS VALUE
# Example: python group_write.py 192.168.1.242 1/1/1 1

from sys import path, argv
path.append('../../')
# Internal
from bof import BOFNetworkError
from bof.layers.knx import *

#-----------------------------------------------------------------------------#
# TUNNEL CONNECTION                                                           #
#-----------------------------------------------------------------------------#

def tunnel_connect(knxnet):
    """Initiates a tunneling connection with the device.
    Creates and send a CONNECT REQUEST with type "TUNNELING CONNECTION".
    """
    conn_req = KNXPacket(type=SID.connect_request, connection_type=0x04)
    conn_req.scapy_pkt.control_endpoint.ip_address, conn_req.scapy_pkt.control_endpoint.port = knxnet.source
    conn_req.scapy_pkt.data_endpoint.ip_address, conn_req.scapy_pkt.data_endpoint.port = knxnet.source
    # conn_req.show2()
    # Retrieve the value of "channel" used for the rest of the exchange.
    response, _ = knxnet.sr(conn_req)
    # response.show2()
    return response.communication_channel_id

def tunnel_disconnect(knxnet, channel):
    """Closes an initiated tunneling connection on ``channel``.
    Creates and send a DISCONNECT REQUEST.
    """
    disco_req = KNXPacket(type=SID.disconnect_request)
    disco_req.ip_address, disco_req.port = knxnet.source
    disco_req.communication_channel_id = channel
    # disco_req.show2()
    response, _ = knxnet.sr(disco_req)
    # response.show2()

#-----------------------------------------------------------------------------#
# GROUP WRITE                                                                 #
#-----------------------------------------------------------------------------#

def group_write(knxnet, channel, group_addr, value):
    """Writes ``value`` to KNX devices at ``group_addr``.
    Sends a TUNNELING REQUEST with a Data Req message.
    Expects a TUNNELING REQUEST in return.
    The exchange must end with a TUNNELING ACK.
    """
    tun_req = KNXPacket(type=SID.tunneling_request, cemi=CEMI.l_data_req)
    tun_req.communication_channel_id = channel
    tun_req.source_address = "15.15.255"
    tun_req.destination_address = group_addr
    tun_req.data = value
    tun_req.show2()
    ack, _ = knxnet.sr(tun_req)
    # ack.show2()
    response, _ = knxnet.receive()
    response.show2()
    # We have to ACK when we receive tunneling requests
    if response.sid == SID.tunneling_request and \
       tun_req.message_code == CEMI.l_data_req:
        ack = KNXPacket(type=SID.tunneling_ack, communication_channel_id=channel)
        # ack.show2()

#-----------------------------------------------------------------------------#
# RUN                                                                         #
#-----------------------------------------------------------------------------#

if len(argv) < 4:
    print("Usage: {0} IP_ADDRESS GROUP_ADDRESS VALUE".format(argv[0]))
    exit(-1)

try:
    knxnet = KNXnet()
    knxnet.connect(argv[1])
    channel = tunnel_connect(knxnet)
    group_write(knxnet, channel, argv[2], int(argv[3]))
    tunnel_disconnect(knxnet, channel)
except BOFNetworkError as bne:
    print(bne)
finally:
    knxnet.disconnect()
