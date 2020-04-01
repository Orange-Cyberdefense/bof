User manual
===========

Overview
--------

Boiboite Opener Framework / Ouvre-Boiboite Framework contains a set of features
to write scripts using industrial network protocols for test and attack
purposes. Functions/tools can be used for:

:Communication: Network connection, initialization and message exchange
                (send/receive)
:Analysis:      Parsing and use of received messages
:Crafting:      Messages forging (valid, invalid, malicious)
:Interaction:   Simple actions such as network discovery, flood, etc.

TL;DR
-----

Import the module and submodules::

    import bof
    from bof import byte
    from bof import knx

Error handling::

    try:
        knx.connect("invalid", 3671)
    except bof.BOFNetworkError as bne:
        print("Connection failure: ".format(str(bne)))

Logging::

    bof.enable_logging()
    bof.log("Cannot send data to {0}:{1}".format(address[0], address[1]), level="ERROR")

Connect to a KNX gateway and send a first message (from the specification)::

    from bof import knx, BOFNetworkError

    knxnet = knx.KnxNet()
    try:
        knxnet.connect("localhost", 13671, init=False)
    except BOFNetworkError as bne:
        print(str(bne))
    frame = knx.KnxFrame(sid="DESCRIPTION REQUEST")
    knxnet.send(bytes(frame))
    response = knxnet.receive()
    print(bytes(response.header.service_identifier))
    # Should print b'\x02\x04' (DESCRIPTION RESPONSE)
    print(bytes(response.body.device_hardware.friendly_name).decode('utf-8'))
    # Should print the name of the device as a string
    knxnet.disconnect()

Advanced usage
--------------

