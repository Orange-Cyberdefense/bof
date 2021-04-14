"""TODO
"""

from bof.layers.raw_scapy import knx as scapy_knx
from bof.packet import BOFPacket
from bof.base import BOFProgrammingError, to_property

from scapy.base_classes import Packet_metaclass
from scapy.packet import Packet

#-----------------------------------------------------------------------------#
# CONSTANTS                                                                   #
#-----------------------------------------------------------------------------#

# Converts Scapy KNX's SERVICE_IDENTIFIER_CODES dict with format
# {byte value: service name} to the opposite, so that the end user can call
# services by their names instead of their values.
SID = type('SID', (object,),
           {to_property(v):k.to_bytes(2, byteorder='big') \
            for k,v in scapy_knx.SERVICE_IDENTIFIER_CODES.items()})()

#-----------------------------------------------------------------------------#
# KNXPacket class                                                             #
#-----------------------------------------------------------------------------#

class KNXPacket(BOFPacket):
    """TODO"""

    def __init__(self, _pkt:bytes=None, type:object=None, **kwargs) -> None:
        """Builds a KNXPacket packet from a byte array or from attributes.

        :param _pkt: KNX frame as byte array to build KNXPacket from.
        :param type: Type of frame to build. Ignored if ``_pkt`` set.
                     Should be a value from ``SID`` dict imported from KNX Scapy
                     implementation as a dict key, a string or as bytes.
        """
        # Initialize Scapy object from bytes or as an empty KNX packet
        if _pkt or not type:
            self.scapy_pkt = scapy_knx.KNX(_pkt=_pkt)
        else:
            self.set_type(type)
        # Handle keyword arguments
        if kwargs:
            print(kwargs)

    def set_type(self, ptype:object) -> None:
        """Format packet according to the specified type (service identifier).

        :param ptype: Type of frame to build. Ignored if ``_pkt`` set.
                      Should be a value from ``SID`` dict imported from KNX Scapy
                      implementation as a dict key, a string or as bytes.
        """
        if isinstance(ptype, str):
            for key, value in scapy_knx.SERVICE_IDENTIFIER_CODES.items():
                if to_property(ptype) == to_property(value):
                    ptype = key.to_bytes(2, byteorder='big')
                    break
        if isinstance(ptype, bytes):
            # TODO
            self.scapy_pkt = scapy_knx.KNX()
        elif isinstance(ptype, Packet):
            self.scapy_pkt = ptype
        elif isinstance(ptype, Packet_metaclass):
            self.scapy_pkt = ptype()
        else:
            raise BOFProgrammingError("Unknown type for KNXPacket ({0})".format(ptype))
