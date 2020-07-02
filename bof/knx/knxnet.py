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

from .. import byte
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
    channel:int
    __init:bool

    #-------------------------------------------------------------------------#
    # Override                                                                #
    #-------------------------------------------------------------------------#

    def connect(self, ip:str, port:int=3671, init:bool=False) -> object:
        """Initialize KNXnet/IP connection over UDP.

        :param ip: IPv4 address as a string with format ("A.B.C.D").
        :param port: Default KNX port is 3671 but can be changed.
        :param init: If set to ``True``, a KNX frame ``CONNECT_REQUEST``
                     is sent when establishing the connection. The other part
                     should reply with a ``CONNECT_RESPONSE`` returned as
                     a ``KnxFrame`` object. Default is ``False``.
        :returns: A ``KnxFrame`` with the parsed ``CONNECT_RESPONSE`` if
                  any, else returns current ``KnxNet`` instance.
        """
        channel = 0
        self.__init = False # Set if we use a connect request
        super().connect(ip, port)
        if init:
            self.__init = True
            init_frame = KnxFrame(type="CONNECT REQUEST")
            init_frame.body.control_endpoint.ip_address._update_value(byte.from_ipv4(self.source[0]))
            init_frame.body.control_endpoint.port._update_value(byte.from_int(self.source[1]))
            init_frame.body.data_endpoint.ip_address._update_value(byte.from_ipv4(self.source[0]))
            init_frame.body.data_endpoint.port._update_value(byte.from_int(self.source[1]))
            response = self.send_receive(bytes(init_frame))
            self.channel = response.body.communication_channel_id.value
            return response
        return self

    def disconnect(self, in_error:bool=False) -> object:
        """Disconnects from KNXnet/IP server. If a CONNECT REQUEST was sent
        when initializing the connection, we close it.

        :param in_error: Boolean to specify whether or not the connection was
                         closed on error, as this method can be called from
                         within the module in case of a network error.
        :returns: A ``DISCONNECT RESPONSE`` as a ``KnxFrame`` object if a
                  ``DISCONNECT REQUEST`` was sent, else None
        :raises BOFNetworkError: if `in_error` is set to `True`.
        """
        response = None
        if self.__init:
            disco_frame = KnxFrame(type="DISCONNECT REQUEST")
            disco_frame.body.communication_channel_id = self.channel
            disco_frame.body.control_endpoint.ip_address._update_value(byte.from_ipv4(self.source[0]))
            disco_frame.body.control_endpoint.port._update_value(byte.from_int(self.source[1]))
            response = self.send_receive(bytes(disco_frame))
            self.channel = 0 # Reset
        super().disconnect(in_error)
        return response

    def send_receive(self, data:bytes, address:tuple=None, timeout:float=1.0) -> object:
        """Overrides ``UDP``'s ``send_receive()`` method so that it returns a
        parsed ``KnxFrame`` object when receiving a datagram instead of a raw
        byte array.

        :param data: Raw byte array or string to send.
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
        
        :param data: Raw byte array or string to send.
        :param address: Address to send ``data`` to, with format
                       tuple ``(ipv4_address, port)``.  If address is not
                       specified, uses the address given to ``connect``.
        :returns: The number of bytes sent, as an integer.
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
