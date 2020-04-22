"""
Network connection
------------------

KNXnet/IP connection features, implementing ``bof.network``'s ``UDP`` class.

KNX usually works over UDP, however KNX specification v2.1 state that TCP can
also be used. The communication between BOF and a KNX object still acts like
a TCP-based protocol, as (almost) every request expects a response.

``KnxNet`` class (for establishing and maintaining a connection) is inherited
from the ``UDP`` class from ``bof.network`` submodule and uses most of its
features. Fill free to change the inheritance to TCP, it may work as long as
the ``TCP`` class mostly follows the same structure as ``UDP`` class.

Usage::

    knxnet = knx.KnxNet()
    knxnet.connect("192.168.0.100", 3671)
    datagram, address = knxnet.receive()
    print(datagram)
    knxnet.disconnect()
"""

from ..network import UDP
from .knxframe import KnxFrame

###############################################################################
# KNX PROTOCOLS AND FRAMES CONSTANTs                                          #
###############################################################################

MULTICAST_ADDR = "224.0.23.12"
PORT = 3671

###############################################################################
# KNXNET/IP NETWORK CONNECTION                                                #
###############################################################################

class KnxNet(UDP):
    """KNXnet/IP communication over UDP with protocol KNX.

    - Data transmission details are in **KNX Standard v2.1 - 03_03_04**.
    - Sent and received datagrams are returned as ``KnxFrame`` objects.
    - Relies on ``bof.network.UDP()``.
    - Only ``connect()`` and ``receive()`` are overriden from class ``UDP``.
    """

    #-------------------------------------------------------------------------#
    # Override                                                                #
    #-------------------------------------------------------------------------#

    def connect(self, ip:str, port:int=3671, init:bool=False) -> object:
        """Initialize KNXnet/IP connection over UDP.

        :param ip: IPv4 address as a string with format ("A.B.C.D").
        :param port: Default KNX port is 3671 but can be changed.
        :param init: If set to ``True``, a KNX frame ``DESCRIPTION_REQUEST``
                     is sent when establishing the connection. The other part
                     should reply with a ``DESCRIPTION_RESPONSE`` returned as
                     a ``KnxFrame`` object. Default is ``False``.
        :returns: A ``KnxFrame`` with the parsed ``DESCRIPTION_RESPONSE`` if
                  any, else returns ``None``.
        """
        super().connect(ip, port)
        if init:
            init_frame = KnxFrame(sid="DESCRIPTION REQUEST")
            init_frame.body.ip_address._update_value(self.source[0])
            init_frame.body.port._update_value(self.source[1])
            return self.send_receive(bytes(init_frame))
        return None

    def send_receive(self, data:bytes, address:tuple=None, timeout:float=1.0) -> object:
        """Overrides ``UDP``'s ``send_receive()`` method so that it returns a
        parsed ``KnxFrame`` object when receiving a datagram instead of a raw
        byte array.

        :param data: Raw byte array to send.
        :param address: Remote network address with format ``(ip, port)``.
        :param timeout: Time out value in seconds, as a float (default 1.0s).
        :returns: A KnxFrame object filled with the content of the received
                  frame.
        :raises BOFProgrammingError: if ``timeout`` is invalid.
        :raises BOFNetworkError: if connection timed out before receiving a packet.
        """
        self.send(data, address)
        return self.receive(timeout)

    def send(self, data, address:tuple=None) -> int:
        """Relies on ``UDP`` to send data. ``UDP.send()`` expects bytes so we
        convert it first if we received data as a ``KnxFrame`` object.
        """
        if isinstance(data, KnxFrame):
            data = bytes(data)
        super().send(data, address)

    def receive(self, timeout:float=1.0) -> object:
        """Overrides ``UDP``'s ``receive()`` method so that it returns a parsed
        ``KnxFrame`` object when receiving a datagram instead of raw byte array.

        :param timeout: Time to wait (in seconds) to receive a frame (default 1s)
        :returns: A parsed KnxFrame with the received frame's representation.
        """
        data, address = super().receive(timeout)
        return KnxFrame(frame=data, source=address)
