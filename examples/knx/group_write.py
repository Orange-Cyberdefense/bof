# BOF usage example using KNXnet/IP
# This script will send a write request to a KNX group address.
# Usage: python group_write.py IP_ADDRESS GROUP_ADDRESS VALUE

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
    conn_req.control_endpoint.ip_address, conn_req.control_endpoint.port = knxnet.source
    conn_req.data_endpoint.ip_address, conn_req.data_endpoint.port = knxnet.source
    conn_req.show2()
    # Retrieve the value of "channel" used for the rest of the exchange.
    response, _ = knxnet.sr(conn_req)
    response.show2()
    return response.communication_channel_id

def tunnel_disconnect(knxnet, channel):
    """Closes an initiated tunneling connection on ``channel``.
    Creates and send a DISCONNECT REQUEST.
    """
    disco_req = KNXPacket(type=SID.disconnect_request)
    disco_req.control_endpoint.ip_address, disco_req.control_endpoint.port = knxnet.source
    disco_req.communication_channel_id = channel
    disco_req.show2()
    response, _ = knxnet.sr(disco_req)
    response.show2()

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
    print(channel)
    tunnel_disconnect(knxnet, channel)
except BOFNetworkError as bne:
    print(bne)
finally:
    knxnet.disconnect()
