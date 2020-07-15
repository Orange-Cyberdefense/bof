"""Network protocol global classes and abstract implementations.

Provides classes for asynchronous network connection management on different
transport protocols, to be used by higher-level protocol implementation classes.
Relies on module ``asyncio``.

:UDP: Implementation of asynchronous UDP communication and packet crafting.

Network connection and example example with raw UDP::

    from bof import UDP
    udp = UDP()
    udp.connect("192.168.1.1", 3671)
    udp.send(b"Hi!")
    udp.disconnect()

.. warning:: Direct initialization of UDP object is not recommended. The user
             should use classes inherited from UDP, such as the KNX protocol
             implementation class (``bof.knx.KnxNet``). Regular network usage
             is the same except for protocol-specific actions and attributes.
             Details are given in the chapter dedicated to the chosen protocol.
"""

import asyncio
from ipaddress import ip_address, IPv4Address
from concurrent import futures
from socket import AF_INET, gaierror
from .base import BOFNetworkError, BOFProgrammingError, log
from . import byte

###############################################################################
# UDP                                                                         #
###############################################################################

#-----------------------------------------------------------------------------#
# Packet structures                                                           #
#-----------------------------------------------------------------------------#

class UDPField(object):
    """Object representation of a UDP field inside a block.

    Contains a set of attributes useful for UDP fields building and
    handling, they may not all be used depending on the type of field.

    :param size: The size of the field (number of bytes in the bytearray)
    :param value: The content of the field (bytearray)
    :param fixed_size: Set to ``True`` if the ``size`` should not be modified
                       automatically when changing the value.
    :param fixed_value: Set to ``True`` if the ``value`` should not be
                        modified automatically inside the module.

    ``fixed_size`` and ``fixed_value`` parameters are set to True when the user
    manually specified a value for them: this manual value should not be
    overwritten by automated field updates.
    """
    _size:int
    _value:bytes
    fixed_size:bool
    fixed_value:bool

    def __init__(self, value=b'', size:int=1, fixed_size:bool=False, fixed_value:bool=False, **kwargs):
        """Initialize a field, requires at least a value to store to the field.

        :param value: Value to store as byte or int
        :param size: Size of the field (number of bytes)
        :param fixed_size: Boolean to state if the size can or cannot be changed.
        :param fixed_value: Boolean to state if the value can be modified.
        :param kwargs: Not used here but subclasses may use more keyword
                       arguments.
        """
        # We need to set this value first
        self.fixed_size = fixed_size
        self._size = max(size, byte.get_size(value)) if not self.fixed_size else size
        self.fixed_value = False # Initialize to false before it fails x)
        self._value = value # Call property setter
        # We set this after we first set a value
        self.fixed_value = fixed_value # Now we set the correct value

    def __str__(self):
        return "<{0}: {1} ({2}b)>".format(type(self).__name__, self._value, self._size)

    #--------------------------------------------------------------------------#
    # Public                                                                   #
    #--------------------------------------------------------------------------#

    def update(self, value):
        """Update field value, only if ``fixed_value`` is set to False.

        :param value: Bytes or int (will be converted to bytes) to use as field
                      value.

        .. warning:: This method should be used mainly when automatically
                     changing field values and not be called directly. Please
                     use properties (getters) instead.
        """
        if not self.fixed_value:
            self._set_value(value)

    #--------------------------------------------------------------------------#
    # Properties                                                               #
    #--------------------------------------------------------------------------#

    @property
    def value(self) -> bytes:
        return self._value
    @value.setter
    def value(self, content) -> None:
        if not self.fixed_value:
            if isinstance(content, bytes):
                self._value = byte.resize(content, self.size)
            elif isinstance(content, str):
                self._value = bytes.fromhex(content)
                self._value = byte.resize(self._value, self.size)
            elif isinstance(content, int):
                self._value = byte.from_int(content, size=self.size)
            else:
                raise BOFProgrammingError("Field value should be bytes, str or int.")

    @property
    def size(self) -> int:
        return self._size
    @size.setter
    def size(self, size:int):
        if not self.fixed_size:
            self._size = size
            self._value = byte.resize(self._value, self._size)

#-----------------------------------------------------------------------------#
# Protocol implementation                                                     #
#-----------------------------------------------------------------------------#

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

    def error_received(self, e):
        """Send disconnect order if error is connection refused.
        Else we let the error occur, it will be logged if logging is enabled.
        """
        if isinstance(e, ConnectionRefusedError) and self.__endpoint:
            self.__endpoint.disconnect(in_error=e)

class UDP(object):
    """UDP protocol endpoint.

    This is the parent class to higher-lever network protocol implementation.
    It can be instantiated as is, however this is not the expected behavior.
    Uses protected ``_UDP`` classes implementing ``asyncio`` UDP handler.
    """
    _transport: object # SelectorDatagramTransport
    _address: tuple # (ip, port)
    _socket:tuple # local (ip, port)
    _queue: object
    _loop: object

    def __init__(self):        
        self._queue = asyncio.Queue()
        self._source = None
        self._transport = None

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def connect(self, ip:str, port:int) -> object:
        """Initialize asynchronous connection using UDP transport on remote
        address specified with `ip` and `port`.

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
        self._loop = asyncio.get_event_loop()
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

    def receive(self, timeout:float=1.0) -> (bytes, tuple):
        """Listen on the network until receiving a packet on the socket or until
        ``timeout``.

        :param timeout: Time out value in seconds,  as a float (default is 1.0s).
        :returns: a tuple ``(data:bytes, address:tuple)`` where address is the
                  remote address and has format ``(ip, port)``.
        :raises BOFProgrammingError: if ``timeout`` is invalid.
        :raises BOFNetworkError: if connection timed out before receiving a packet.

        Example::

            response, address = udp.receive()
        """
        data, address = self._loop.run_until_complete(self.__listen_once(timeout))
        log("Received from {0}:{1} : {2}".format(address[0], address[1], data))
        return data, address

    def send_receive(self, data:bytes, address:tuple=None, timeout:float=1.0) -> (bytes, tuple):
        """sends a packet to ``address`` and wait for a response until
        ``timeout``. Clever implementation of TCP over UDP, because this is
        exactly what some BMS network protocols do (yay, KNX!).
        
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

    def disconnect(self, in_error:bool=False) -> None:
        """Closes the transport link.

        :param in_error: Boolean to specify whether or not the connection was
                         closed on error, as this method can be called from
                         within the module in case of a network error.
        :raises BOFNetworkError: if `in_error` is set to `True`.
        """
        if self._transport:
            self._transport.close()
            self._transport = None
        if in_error:
            self._handle_exception(in_error, "Connection ended unexpectedly")
        else:
            log("Disconnected.")

    #-------------------------------------------------------------------------#
    # Protected                                                               #
    #-------------------------------------------------------------------------#

    def _receive(self, data:bytes, address:tuple) -> None:
        """Receives raw datagram and adds it to queue for processing.
        
        .. warning:: Should not be called directly.
        """
        try:
            self._queue.put_nowait((data, address))
        except asyncio.QueueFull:
            log("Queue is full", "ERROR")
            raise BOFNetworkError("Queue is full")

    def _handle_exception(self, exception:object, message:str) -> None:
        """Log exception and raise BOF-defined network exception instead.

        .. seealso:: bof.base.BOFNetworkError"""
        log("Exception occurred: {0}".format(repr(exception)), "ERROR")
        message = "{0} ({1})".format(message, repr(exception))
        raise BOFNetworkError(message) from None

    #-------------------------------------------------------------------------#
    # Private                                                                 #
    #-------------------------------------------------------------------------#

    async def __listen_once(self, timeout:float=1.0) -> (bytes, tuple):
        """Listen until a packet is received from UDP connection or
        until ``timeout`` (default: 1 second).
        """
        if not isinstance(timeout, float) and not isinstance(timeout, int):
            raise BOFProgrammingError("Timeout expects a float (seconds)")
        try:
            data, address = await asyncio.wait_for(self._queue.get(),
                                                   timeout=float(timeout))
        except futures._base.TimeoutError as te:
            self._handle_exception(te, "Connection timeout")
        return data, address

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def transport(self):
        """Get UDP transport object ``SelectorDatagramTransport``.
        Relies on Python's builtin ``asyncio`` module.
        """
        return self._transport
    @transport.setter
    def transport(self, value):
        """Set UDP transport object ``SelectorDatagramTransport``.
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
