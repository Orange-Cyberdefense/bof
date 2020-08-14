"""
Network connection
------------------

OPC UA Binary connection features, implementing ``bof.network``'s ``TCP`` class.

OPC UA protocol works on a TCP base, and supports two protocols : binary and
web-based. The binary protocol offers the best performance/least overhead, so
this is the one used in most implementations.

Usage::

    opcuanet = opcua.OpcuaNet()
    opcuanet.connect("opc.tcp://localhost:4840")
    data = opcuanet.receive()
    print(data)
    opcuanet.disconnect()
"""

from .. import byte
from ..network import TCP
from .opcuaframe import OpcuaFrame

from urllib.parse import urlparse
from ipaddress import ip_address, IPv4Address
from socket import gethostbyname, gaierror


###############################################################################
# OPC AU PROTOCOLS AND FRAMES CONSTANTs                                       #
###############################################################################

PORT = 4840
byte.set_byteorder('little')

###############################################################################
# OPC UA Binary NETWORK CONNECTION                                            #
###############################################################################

class OpcuaNet(TCP):
    """OPC UA Binary communication over TCP.

    - Sent and received data are returned as ``OpcuaFrame`` objects.
    - Relies on ``bof.network.TCP()``.
    - Only ``connect()`` and ``receive()`` are overriden from class ``TCP``.
    """

    #-------------------------------------------------------------------------#
    # Override                                                                #
    #-------------------------------------------------------------------------#

    def tcp_connect(self, ip:str, port:int) -> object:
        """Initialize a connection over TCP via OpcuaNet object.

        :param ip: IPv4 address as a string with format ``A.B.C.D``.
        :param port: Port number as an integer.
        :returns: TODO:
        """
        super().connect(ip, port)
        return

    def connect(self, endpoint_url:str) -> object:
        """Initialize OPC UA Binary connection over TCP.

        :param endpoint_url: OPC UA endpoint with format "opc.tcp://localhost:4840".
        :returns: TODO:
        """
        ip, port = self._get_address_from_url(endpoint_url)
        tcp_connect(ip, port)
        self._open_connection((ip, port), endpoint_url)
        return

    def disconnect(self, in_error:bool=False) -> object:
        return

    def send_receive(self, data:bytes, address:tuple=None, timeout:float=1.0) -> object:
        """Overrides ``TCP``'s ``send_receive()`` method so that it returns a
        parsed ``OpcuaFrame`` object when receiving data instead of a raw
        byte array.

        :param data: Raw byte array or string to send.
        :param address: Remote network address with format ``(ip, port)``.
        :param timeout: Time out value in seconds, as a float (default 1.0s).
        :returns: An OpcuaFrame object filled with the content of the received
                  frame.
        :raises BOFProgrammingError: if ``timeout`` is invalid.
        :raises BOFNetworkError: if connection timed out before receiving a packet.
        """
        self.send(data, address)
        return self.receive(timeout)

    def send(self, data, address:tuple=None) -> int:
        """Relies on ``TCP`` to send data. ``TCP.send()`` expects bytes so we
        convert it first if we received data as an ``OpcuaFrame`` object.
        
        :param data: Raw byte array or string to send.
        :param address: Address to send ``data`` to, with format
                       tuple ``(ipv4_address, port)``.
        :returns: The number of bytes sent, as an integer.
        """
        if isinstance(data, OpcuaFrame):
            data = bytes(data)
        super().send(data, address)
        return

    def receive(self, timeout:float=1.0) -> object:
        """Overrides ``TCP``'s ``receive()`` method so that it returns a parsed
        ``OpcuaFrame`` object when receiving a datagram instead of raw byte array.

        :param timeout: Time to wait (in seconds) to receive a frame (default 1s)
        :returns: A parsed OpcuaFrame with the received frame's representation.
        """
        data, address = super().receive(timeout)
        return OpcuaFrame(bytes=data)
    
    #-------------------------------------------------------------------------#
    # Internal (should not be used by end users)                              #
    #-------------------------------------------------------------------------#

    def _open_connection(self, address:tuple, endpoint_url:str):
        """Sends a HEL to an OPC UA endpoint and waits for an ACK response.
        This is the first step of OPC UA communication establishement, as
        described in OPC UA's ``IEC 62541-6`` specification.

        :param address: Address to send ``data`` to, with format
                       tuple ``(ipv4_address, port)``.
        :param endpoint_url: OPC UA endpoint with format "opc.tcp://localhost:4840".
                             Needed as parameter in HEL frame.
        :return: An ``OpcuaFrame`` with the parsed ``ACK`` response if any.
        """
        frame = OpcuaFrame(type="HEL")
        frame.header.is_final.value = b"F"
        frame.body.protocol_version.value = byte.from_int(0)
        frame.body.receive_buffer_size.value = byte.from_int(65535)
        frame.body.send_buffer_size.value = byte.from_int(65535)
        frame.body.max_message_size.value = byte.from_int(0)
        frame.body.max_chunk_count.value = byte.from_int(0)
        frame.body.endpoint_url_length.value =  byte.from_int(len(endpoint_url))
        frame.body.endpoint_url.size = len(endpoint_url)
        frame.body.endpoint_url.value = endpoint_url
        response = self.send_receive(bytes(frame), address)
        return response
    
    def _open_secure_channel(self):
        """Sends an OPN request to an OPC UA endpoint and waits for the server
        negociated parameters in response.
        This is the second step of OPC UA communication establishement, as
        described in OPC UA's ``IEC 62541-6`` specification.
        """
        return
    
    def _create_session(self):
        return

    def _get_address_from_url(self, url):
        """Parses an url for ip and port.
        
        :param url: an url to parse.
        :return: tuple (host, port)
                 port takes None values if not found
                 host keeps hostname value if no IP associated
        """
        parsed_uri = urlparse(url)
        host = parsed_uri.hostname
        port = parsed_uri.port
        if host and not isinstance(host, IPv4Address):
            try:
                host = gethostbyname(host)
            except(gaierror):
                pass
        return (host, port)
