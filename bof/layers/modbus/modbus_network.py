"""
Network connection
------------------

Modbus TCP/IP connection features, implementing ``bof.network``'s ``TCP`` class.

The ``ModbusNet`` class translates ``ModbusPacket`` packet objects and raw Scapy
packets to bytes to send them, and received bytes to ``ModbusPacket`` objects.

Usage::

    modbus_net = ModbusNet()
    modbus_net.connect("192.168.1.242")
    modbus_req = ModbusPacket(type=MODBUS_TYPES.REQUEST, function=b'\x01')
    modbus_resp = modbus_net.sr(modbus_req)
    modbus_resp.show2()
    modbus_net.disconnect()
"""

###############################################################################
# ModbusNet class                                                             #
###############################################################################
from scapy.compat import raw
from scapy.packet import Packet

from bof import TCP
from bof.layers.modbus.modbus_packet import ModbusPacket, MODBUS_TYPES


class ModbusNet(TCP):
    """Modbus TCP/IP communication.
        Relies on ``bof.network.TCP()``.

        Sent and received datagrams are returned as ``ModbusPacket()`` objects.

        ..seealso:: Details on TCP exchange:
        * MODBUS Application Protocol Specification V1.1b3 - 1.1 Introduction
        * MODBUS Messaging on TCP/IP Implementation Guide V1.0b
    """

    def connect(self, ip: str, port: int = 502):
        """Connects to a Modbus Server (opens socket). Default port is ``3671``.

        :param ip: IPv4 address as a string with format ``A.B.C.D``.
        :param port: Modbus port. Default is ``502``.
        :returns: The Modbus connection object (this instance).
        :raises BOFNetworkError: if connection fails.
        """
        super().connect(ip, port)
        return self

    def send(self, data, address: tuple = None) -> int:
        """Converts BOF and Scapy frames to bytes to send.
        Relies on ``TCP`` class to send data.

        :param data: Data to send as ``ModbusPacket``, Scapy ``Packet``, string
                     or bytes. Will be converted to bytes anyway.
        :param address: Address to send ``data`` to, with format ``(ip, port)``.
                        If address is not specified, uses the address given to
                        `` connect``.
        :returns: The number of bytes sent, as an integer.
        """
        if isinstance(data, ModbusPacket):
            data = bytes(data)
        elif isinstance(data, Packet):
            data = raw(data)
        return super().send(data, address)
        # TODO: add transaction id incrementation + unitid (+ name ?)

    def receive(self, timeout: float = 1.0) -> object:
        """Converts received bytes to a parsed ``ModbusPacket`` object.

        :param timeout: Time to wait to receive a frame (default is 1 sec)
        :returns: A ``ModbusPacket`` object and the sender address.
        """
        data, address = super().receive(timeout)
        return ModbusPacket(_pkt=data, type=MODBUS_TYPES.RESPONSE), address
