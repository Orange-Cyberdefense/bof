"""
Network connection
------------------

KNXnet/IP connection features, implementing ``bof.network``'s ``UDP`` class.

The ``KnxNet`` class translates ``KNXPacket`` packet objects and raw Scapy
packets to bytes to send them, and received bytes to ``KNXPacket`` objects.

KNX usually works over UDP, however KNX specification v2.1 state that TCP can
also be used. The communication between BOF and a KNX device still acts like
a TCP-based protocol, as (almost) every request expects a response.

Usage::

    knxnet = KNXnet()
    knxnet.connect("192.168.1.242")
    data, addr = knxnet.sr(KNXPacket(type=SID.description_request))
    data.show2()
    knxnet.disconnect()
"""

# Scapy
from scapy.compat import raw
from scapy.packet import Packet
# Internal
from bof.network import UDP
from .knx_packet import KNXPacket

###############################################################################
# KNXNet class                                                                #
###############################################################################

class KNXnet(UDP):
    """KNXnet/IP communication over UDP with protocol KNX.
    Relies on ``bof.network.UDP()``.

    Sent and received datagrams are returned as ``KNXPacket()`` objects.

    ..seealso:: Details on data exchange: **KNX Standard v2.1 - 03_03_04**.
    """
    sequence_counter = None
    
    def connect(self, ip:str, port:int=3671) -> object:
        """Connect to a KNX device (opens socket). Default port is ``3671``.

        :param ip: IPv4 address as a string with format ``A.B.C.D``.
        :param port: KNX port. Default is ``3671``.
        :returns: The KNXnet connection object (this instance).
        :raises BOFNetworkError: if connection fails.
        """
        super().connect(ip, port)
        self.sequence_counter = 0
        return self

    def send(self, data:object, address:tuple=None) -> int:
        """Converts BOF and Scapy frames to bytes to send.
        Relies on ``UDP`` class to send data.

        :param data: Data to send as ``KNXPacket``, Scapy ``Packet``, string
                     or bytes. Will be converted to bytes anyway.
        :param address: Address to send ``data`` to, with format ``(ip, port)``.
                        If address is not specified, uses the address given to
                        `` connect``.
        :returns: The number of bytes sent, as an integer.
        """
        if isinstance(data, KNXPacket):
            data = bytes(data)
        elif isinstance(data, Packet):
            data = raw(data)
        return super().send(data, address)

    def receive(self, timeout:float=1.0) -> object:
        """Converts received bytes to a parsed ``KNXPacket`` object.

        :param timeout: Time to wait to receive a frame (default is 1 sec)
        :returns: A ``KNXPacket`` object.
        """
        data, address = super().receive(timeout)
        return KNXPacket(data), address
