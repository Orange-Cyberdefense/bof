"""Network protocol global classes and abstract implementations.

Provides classes for asynchronous network connection management on different
transport protocols, to be used by higher-level protocol implementation classes.
Relies on module ``asyncio``.

:UDP: Implementation of asynchronous UDP communication and packet crafting.
:TCP: Implementation of asynchronous TCP communication and packet crafting.

Both classes rely on internal class ``_Transport``, which should not be
instantiated.

Network connection and exchange example with raw UDP::

    from bof import UDP
    udp = UDP()
    udp.connect("192.168.1.1", 3671)
    udp.send(b"Hi!")
    udp.disconnect()

Usage is the same with raw TCP.

.. warning:: Direct initialization of TCP/UDP object is not recommended.
             The user should use BOF network classes inherited from
             TCP/UDP (e.g. ``KNXnet`` for the ``KNX`` protocol).
"""

import asyncio
from ipaddress import ip_address, IPv4Address
from concurrent import futures
from socket import AF_INET, SOCK_DGRAM, IPPROTO_IP, IP_MULTICAST_TTL, \
    SOL_SOCKET, SO_BROADCAST
from socket import socket, timeout as sotimeout, gaierror
from struct import pack
# Internal
from .base import BOFNetworkError, BOFProgrammingError, log

###############################################################################
# Global network-related constants and functions                              #
###############################################################################

DEFAULT_IFACE="eth0"

def IS_IP(ip: str):
    """Check that ip is a valid IPv4 address."""
    try:
        ip_address(ip)
    except ValueError:
        raise BOFProgrammingError("Invalid IP {0}".format(ip)) from None

###############################################################################
# Asyncio classes for UDP and TCP                                             #
###############################################################################

class _UDP(asyncio.DatagramProtocol):
    """UDP protocol implementation interface from asyncio builtin UDP handler.
    Will be called from protocol implementation class.
    Not to be instantiated outside module (and outside UDP class).
    """
    __endpoint = None

    def __init__(self, endpoint):
        """Register instance of endpoint to process received data."""
        self.__endpoint = endpoint

    def connection_made(self, transport):
        """Register transport information after connection is established."""
        self.__endpoint.transport = transport

    def connection_lost(self, exception):
        """Request endpoint to disconnect when connection is lost."""
        if self.__endpoint:
            self.__endpoint.disconnect()

    def datagram_received(self, data, address):
        """Send received datagram to endpond for processing."""
        self.__endpoint._receive(data, address)

class _TCP(asyncio.Protocol):
    """TCP protocol implementation interface from asyncio builtin TCP handler.
    Will be called from protocol implementation class.
    Not to be instantiated outside module (and outside TCP class).
    """
    __endpoint = None

    def __init__(self, endpoint):
        """Register instance of endpoint to process received data."""
        self.__endpoint = endpoint

    def connection_made(self, transport):
        """Register transport information after connection is established."""
        self.__endpoint.transport = transport

    def connection_lost(self, exception):
        """Request endpoint to disconnect when connection is lost."""
        if self.__endpoint:
            self.__endpoint.disconnect()

    def data_received(self, data):
        """Send received data to endpoint for processing."""
        self.__endpoint._receive(data, None)
    
    def eof_received(self):
        """Send disconnect order when the other end reaches EOF"""
        if self.__endpoint:
            self.__endpoint.disconnect()

###############################################################################
# Transport base class                                                        #
###############################################################################

class _Transport(object):
    """Transport protocol endpoint. UDP and TCP endpoint are inheriting it.
    Relies on _TCP and _UDP asyncio classes, specified in the constructor.
    Transport class shall never be instantiated directly.
    """
    def __init__(self):        
        self._queue = asyncio.Queue()
        self._source = None
        self._transport = None
        self._socket = None

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def connect(self, ip:str, port:int) -> object:
        """Connect to a server at address ``ip``:``port``. (ABSTRACT)
        As asyncio classes have different methods to initialize a connection
        depending on the protocol, this method should be always implemented
        in subclasses.
        """
        raise NotImplementedError("Method must be implemented in subclasses")

    def disconnect(self) -> None:
        """Closes the transport link if it exists."""
        if self._transport:
            self._transport.close()
            self._transport = None
            log("Disconnected.")

    def send(self, data:bytes, address:tuple=None) -> int:
        """Sends ``data`` to ``address``. (ABSTRACT)
        As asyncio classes have different methods to send data depending on
        the protocol, this method should always be implemented in subclasses.
        """
        raise NotImplementedError("Method must be implemented in subclasses")

    def receive(self, timeout:float=1.0) -> (bytes, tuple):
        """Listen on the network until receiving a packet or until ``timeout``.

        :param timeout: Time out value in seconds,  as a float (default is 1.0s).
        :returns: A tuple ``(data:bytes, address:tuple)`` where address is the
                  remote address and has format ``(ip, port)``.
        :raises BOFProgrammingError: if ``timeout`` is invalid.
        :raises BOFNetworkError: if connection timed out before receiving a packet.

        Example::

            response, address = tcp.receive()
            response, address = udp.receive()
        """
        data, address = self._loop.run_until_complete(self.__listen_once(timeout))
        log("Received from {0}:{1} : {2}".format(address[0], address[1], data))
        return data, address

    def send_receive(self, data:bytes, address:tuple=None, timeout:float=1.0) -> (bytes, tuple):
        """Sends a packet to ``address``, wait for a response until ``timeout``.

        :param data: Raw byte array or string to send.
        :param address: Remote network address with format tuple ``(ip, port)``.
        :param timeout: Time out value in seconds,  as a float (default is 1.0s).
        :returns: a tuple ``(data:bytes, address:tuple)`` where address is the
                  remote address and has format ``(ip, port)``.
        :raises BOFProgrammingError: if ``timeout`` is invalid.
        :raises BOFNetworkError: if connection timed out before receiving a packet.

        Example::

            result, _ = udp.send_receive("test_send_receive", timeout=10)
            result = result.decode('utf-8') # with echo server: "test_send_receive"
        """
        self.send(data, address)
        data, address = self.receive(timeout)
        return data, address

    def sr(self, data:bytes, address:tuple=None, timeout:float=1.0) -> (bytes, tuple):
        """Shortcut to ``send_receive()`` method. Arguments are the same."""
        return self.send_receive(data, address, timeout)

    #-------------------------------------------------------------------------#
    # Protected                                                               #
    #-------------------------------------------------------------------------#

    def _handle_exception(self, loop:object, context) -> None:
        """Log exception and raise BOF-defined network exception instead.

        .. seealso:: bof.base.BOFNetworkError"""
        message = context if isinstance(context, str) else context.get("exception", context["message"])
        log("Exception occurred: {0}".format(message), "ERROR")
        # self.disconnect()
        raise BOFNetworkError(message) from None

    def _receive(self, data:bytes, address:tuple) -> None:
        """Receives a raw datagram and adds it to queue for processing.
        
        .. warning:: Should not be called directly.
        """
        try:
            self._queue.put_nowait((data, address))
        except asyncio.QueueFull:
            log("Queue is full", "ERROR")
            raise BOFNetworkError("Queue is full")

    def _argument_check(data:bytes, address:tuple) -> None:
        """Check that parameters to send ``data`` to an ``address`` are valid.
        If so, they are changed to appropriate format for sockets.

        :param data: Raw byte array or string to send.
        :param address: Remote network address with format tuple ``(ip, port)``.
        :returns: data, address
        :raises BOFNetworkError: If either parameter is invalid.
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            else:
                data = bytes(data)
        except TypeError:
            raise BOFProgrammingError("Invalid data type (must be bytes).") from None
        try:
            address = str(ip_address(address[0])), address[1]
        except (ValueError, TypeError):
            raise BOFProgrammingError("Invalid address {0}".format(address)) from None
        return data, address
        
    #-------------------------------------------------------------------------#
    # Private                                                                 #
    #-------------------------------------------------------------------------#

    async def __listen_once(self, timeout:float=1.0) -> (bytes, tuple):
        """Listen until a packet is received or until ``timeout``."""
        if not isinstance(timeout, float) and not isinstance(timeout, int):
            raise BOFProgrammingError("Timeout expects a float (seconds)")
        try:
            data, address = await asyncio.wait_for(self._queue.get(), timeout=float(timeout))
            address = address if address else self._address
        except (futures._base.TimeoutError, asyncio.exceptions.TimeoutError) as te:
            self._handle_exception(te, "Connection timeout")
        return data, address

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def is_connected(self):
        """Returns true if a connection has been established.
        Relies on the values of _socket and _transport to find out.
        """
        return True if self._socket and self._transport else False

    @property
    def transport(self):
        """Get transport object depending on the protocol.
        Relies on Python's builtin ``asyncio`` module.
        """
        return self._transport
    @transport.setter
    def transport(self, value):
        """Set transport object depending on the protocol.
        Relies on Python's builtin ``asyncio`` module.
        """
        self._transport = value

    @property
    def source(self):
        """Get source information on a socket with format tuple
        ``(ipv4_source_address:str, source_port:int)``.
        Requires the connection to be established.
        Relies on Python's builtin ``socket`` module.
        """
        return self._socket.getsockname()

    @property
    def source_address(self) -> str:
        """Get source IPv4 address information using source property.
        Requires the connection to be established.
        """
        return self.source[0]

    @property
    def source_port(self) -> int:
        """Get source port information using source property.
        Requires the connection to be established.
        """
        return self.source[1]

###############################################################################
# UDP                                                                         #
###############################################################################

class UDP(_Transport):
    """UDP protocol endpoint, inheriting from Transport base class.

    This is the parent class to higher-lever network protocol implementation.
    It can be instantiated as is, however this is not the expected behavior.
    Uses protected ``_UDP`` classes implementing ``asyncio`` UDP handler.

    .. warning:: Should not be instantiated directly.
    """

    #-------------------------------------------------------------------------#
    # Static                                                                  #
    #-------------------------------------------------------------------------#    
    
    @staticmethod
    def multicast(data:bytes, address:tuple, timeout:float=1.0) -> list:
        """Sends a multicast request to specified ip address and port (UDP).

        Expects devices subscribed to the address to respond and return
        responses as a list of frames with their source. Opens its own socket.

        :param data: Raw byte array or string to send.
        :param address: Remote network address with format tuple ``(ip, port)``.
        :param timeout: Time out value in seconds,  as a float (default is 1.0s).
        :returns: A list of tuples with format ``(response, (ip, port))``.
        :raises BOFNetworkError: If multicast parameters are invalid.

        Example::

           devices = UDP.multicast(b'\x06\x10...', ('224.0.23.12', 3671))
        """
        responses = []
        ttl = pack('b', 1)
        data, address = UDP._argument_check(data, address)
        try:
            sock = socket(AF_INET, SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, ttl)
            sock.sendto(data, address)
            while True:
                response, sender = sock.recvfrom(1024)
                responses.append((response, sender))
        except OverflowError as exc: # Raised when port invalid
            sock.close()
            raise BOFProgrammingError(str(exc))
        except sotimeout as te:
            pass
        sock.close()
        return responses

    @staticmethod
    def broadcast(data:bytes, address:tuple, timeout:float=1.0) -> list:
        """Broadcasts a request and waits for responses from devices (UDP).

        :param data: Raw byte array or string to send.
        :param address: Remote network address with format tuple ``(ip, port)``.
        :param timeout: Time out value in seconds, as a float (default is 1.0s).
        :returns: A list of tuples with format ``(response, (ip, port))``.
        :raises BOFNetworkError: If multicast parameters are invalid.

        Example::

           devices = UDP.broadcast(b'\x06\x10...', ('192.168.1.255', 3671))
        """
        responses = []
        data, address = UDP._argument_check(data, address)
        # Broadcast request
        try:
            sock = socket(AF_INET, SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            sock.sendto(data, address)
            while True:
                response, sender = sock.recvfrom(1024)
                responses.append((response, sender))
        except OverflowError as exc: # Raised when port invalid
            sock.close()
            raise BOFProgrammingError(str(exc))
        except sotimeout as te:
            pass
        sock.close()
        return responses
        
    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#    

    def connect(self, ip:str, port:int) -> object:
        """Initialize asynchronous connection using UDP on ``ip``:``port``.

        :param ip: IPv4 address as a string with format ``A.B.C.D``.
        :param port: Port number as an integer.
        :returns: The instance of the UDP class created,
        :raises BOFNetworkError: if connection fails.

        Example::

            udp = bof.UDP().connect("127.0.0.1", 13671)
        """
        ip = "127.0.0.1" if ip == "localhost" else ip
        if isinstance(ip, IPv4Address):
            ip = str(ip)
        if port not in range(0, 65535):
            raise BOFNetworkError("Invalid port number.")
        self._loop = asyncio.get_event_loop()
        self._loop.set_exception_handler(self._handle_exception)
        try:
            ip_address(ip) # Check if IP is valid
            connect = self._loop.create_datagram_endpoint(lambda: _UDP(self),
                                                          remote_addr=((ip, port)),
                                                          family=AF_INET,
                                                          allow_broadcast=True)
            transport, protocol = self._loop.run_until_complete(connect)
        except (gaierror, OverflowError, ValueError) as e:
            self._handle_exception(e, "Connection failed")
            return None
        self._address = (ip, port)
        self._socket = self._transport.get_extra_info('socket')
        log("Connected to {0}:{1}".format(ip, port))
        return self

    def send(self, data:bytes, address:tuple=None) -> int:
        """Send ``data`` to ``address`` over UDP.

        :param data: Raw byte array or string to send. 
        :param address: Address to send ``data`` to, with format
                        tuple ``(ipv4_address, port)``.  If address is not 
                        specified, uses the address given to ``connect``.
        :returns: The number of bytes sent, as an integer.

        Example::

            udp.send("test_send")
            udp.send(b'\x06\x10\x02\x03')
        """
        if type(data) == str:
            bdata = data.encode('utf-8')
        else:
            bdata = data
        address = address if address else self._address
        if not self._transport:
            log("Cannot send data to {0}:{1}".format(address[0], address[1]))
            return 0
        try:
            self._transport.sendto(bdata, address)
        except TypeError as te:
            raise BOFNetworkError(str(te)) from None
        log("Send to {0}:{1} : {2}".format(address[0], address[1], data))
        return len(bdata)

###############################################################################
# TCP                                                                         #
###############################################################################

class TCP(_Transport):
    """TCP protocol endpoint.

    This is the parent class to higher-lever network protocol implementation.
    It can be instantiated as is, however this is not the expected behavior.
    Uses protected ``_TCP`` classes implementing ``asyncio`` TCP handler.

    .. warning:: Should not be instantiated directly.
    """

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def connect(self, ip:str, port:int) -> object:
        """Initialize asynchronous connection using TCP on ``ip``:``port``.

        :param ip: IPv4 address as a string with format ``A.B.C.D``.
        :param port: Port number as an integer.
        :returns: The instance of the TCP class created,
        :raises BOFNetworkError: if connection fails.

        Example::

            tcp = bof.TCP().connect("127.0.0.1", 4840)
        """
        ip = "127.0.0.1" if ip == "localhost" else ip
        if isinstance(ip, IPv4Address):
            ip = str(ip)
        self._loop = asyncio.get_event_loop()
        self._loop.set_exception_handler(self._handle_exception)
        try:
            ip_address(ip) # Check if IP is valid
            connect = self._loop.create_connection(lambda: _TCP(self),
                                                           host=ip,
                                                           port=port,
                                                           family=AF_INET)
            transport, protocol = self._loop.run_until_complete(connect)
        except (gaierror, OverflowError, ValueError, ConnectionRefusedError) as e:
            self._handle_exception(e, "Connection failed")
            return None
        self._address = (ip, port)
        self._socket = self._transport.get_extra_info('socket')
        log("Connected to {0}:{1}".format(ip, port))
        return self

    def send(self, data:bytes, address:tuple=None) -> int:
        """Send ``data`` to ``address`` over TCP.

        :param data: Raw byte array or string to send. 
        :param address: Address to send ``data`` to, with format
                        tuple ``(ipv4_address, port)``.  If address is not 
                        specified, uses the address given to ``connect``.
        :returns: The number of bytes sent, as an integer.

        Example::

            tcp.send("test_send")
            tcp.send(b'\x06\x10\x02\x03')
        """
        if type(data) == str: # allow send('str') as well as send(b'str')
            bdata = data.encode('utf-8')
        else:
            bdata = data
        address = address if address else self._address
        if not self._transport:
            log("Cannot send data to {0}:{1}".format(address[0], address[1]))
            return 0
        try:
            self._transport.write(bdata)
        except TypeError as te:
            raise BOFNetworkError(str(te)) from None
        log("Send to {0}:{1} : {2}".format(address[0], address[1], data))
        return len(bdata)
