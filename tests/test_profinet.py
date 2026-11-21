"""unittest for Profinet DCP implementation ``bof.layers.profinet``"""

import unittest
from ipaddress import IPv4Address
from unittest import mock
from scapy.layers.l2 import Ether, Dot1Q
from scapy.contrib.pnio import ProfinetIO
from scapy.contrib.pnio_dcp import (
    DCP_SERVICE_ID,
    DCP_SERVICE_TYPE,
    DCP_SERVICE_ID_IDENTIFY,
    DCP_RESPONSE,
    DCP_IDENTIFY_RESPONSE_FRAME_ID,
    ProfinetDCP,
    DCPNameOfStationBlock,
    DCPManufacturerSpecificBlock,
    DCPIPBlock,
    DCPDeviceIDBlock,
)

from bof import BOFProgrammingError
from bof.layers import profinet
from bof.layers.profinet import profinet_functions

class Test01PNDCPPacket(unittest.TestCase):
    """Test class for PNDCP packet create."""
    def test_0101_profinet_packet_create_identify(self):
        """Test that we can create a PNDCP multicast packet."""
        pkt = profinet.create_identify_packet()
        self.assertEqual(DCP_SERVICE_ID[pkt["ProfinetDCP"].service_id],
                         "Identify")
        self.assertEqual(DCP_SERVICE_TYPE[pkt["ProfinetDCP"].service_type],
                         "Request")

class Test02LLDPSend(unittest.TestCase):
    """Test class for PNDCP packet send."""
    def test_0201_pndcp_packet_send_default(self):
        """Test that nothing wrong happens when sending packet."""
        with self.assertRaises(BOFProgrammingError): # Test not run as sudo
            profinet.send_identify_request()

class Test03LLDPDevice(unittest.TestCase):
    """Test class for LLDP device objects."""
    def test_0301_pndcp_device_raise(self):
        """Test that we cannot create a PNDCP device with request and not response."""
        pkt = profinet.create_identify_packet()
        with self.assertRaises(BOFProgrammingError):
            device = profinet.ProfinetDevice(pkt)


def make_identify_reply(src="aa:bb:cc:dd:ee:ff", name=b"plc-1", ip="10.0.0.5",
                        vlan=False):
    """Build a whole sniffed Identify response packet.

    AsyncSniffer.results holds entire packets (Ether/ProfinetIO/ProfinetDCP),
    optionally encapsulated in 802.1Q, exactly like real replies on the wire.
    """
    if vlan:
        eth = Ether(src=src, dst=profinet.MULTICAST_MAC,
                    type=profinet.ETHER_TYPE_VLAN) / \
              Dot1Q(vlan=1, type=profinet.ETHER_TYPE_PROFINET)
    else:
        eth = Ether(src=src, dst=profinet.MULTICAST_MAC,
                    type=profinet.ETHER_TYPE_PROFINET)
    return eth / \
        ProfinetIO(frameID=DCP_IDENTIFY_RESPONSE_FRAME_ID) / \
        ProfinetDCP(service_id=DCP_SERVICE_ID_IDENTIFY,
                    service_type=DCP_RESPONSE, xid=0x1366b490) / \
        DCPNameOfStationBlock(name_of_station=name) / \
        DCPManufacturerSpecificBlock(device_vendor_value=b"et200sp") / \
        DCPIPBlock(ip=ip, netmask="255.255.255.0", gateway="10.0.0.1") / \
        DCPDeviceIDBlock(vendor_id=0x002a, device_id=0x0313)


def patched_send_identify(replies, captured):
    """Monkeypatch root check, AsyncSniffer and sendp in profinet_functions.

    Returns a context manager; ``captured`` is filled with sniffer/sendp usage.
    """
    class FakeSniffer:
        """Stand-in for AsyncSniffer: results prefilled with sniffed packets."""
        def __init__(self, *args, **kwargs):
            captured["sniffer_kwargs"] = kwargs
            self.results = list(replies)
        def start(self):
            captured["started"] = True
        def join(self):
            captured["joined"] = True

    def fake_sendp(*args, **kwargs):
        captured["sendp_calls"] = captured.get("sendp_calls", 0) + 1

    return mock.patch.multiple(profinet_functions,
                               geteuid=lambda: 0,
                               AsyncSniffer=FakeSniffer,
                               sendp=fake_sendp)


class Test04SendIdentifyRequest(unittest.TestCase):
    """send_identify_request() must build devices from whole sniffed packets."""

    def run_send_identify(self, replies):
        captured = {}
        with patched_send_identify(replies, captured):
            devices = profinet.send_identify_request(iface="eth0", timeout=1)
        return devices, captured

    def test_0401_device_mac_address_from_sniffed_packet(self):
        """A device built from a sniffed reply gets mac_address == Ether.src."""
        reply = make_identify_reply(src="aa:bb:cc:dd:ee:ff", name=b"plc-1",
                                    ip="10.0.0.5")
        devices, captured = self.run_send_identify([reply])
        self.assertEqual(len(devices), 1)
        device = devices[0]
        # Acceptance criterion: full packet passed, Ether layer is visible
        self.assertEqual(device.mac_address, reply["Ether"].src)
        self.assertEqual(device.mac_address, "aa:bb:cc:dd:ee:ff")
        # Non-regression: the rest of parse() still works on the full packet
        self.assertEqual(device.name, "plc-1")
        self.assertEqual(device.description, "et200sp")
        self.assertEqual(device.ip_address, "10.0.0.5")
        self.assertEqual(device.ip_netmask, "255.255.255.0")
        self.assertEqual(device.ip_gateway, "10.0.0.1")
        self.assertEqual(device.vendor_id, "SIEMENS AG")
        self.assertEqual(device.device_id, 0x0313)
        # The request was actually sent and the sniffer lifecycle was used
        self.assertEqual(captured["sendp_calls"], 1)
        self.assertTrue(captured["started"])
        self.assertTrue(captured["joined"])
        # The lfilter handed to the sniffer accepts this reply (realistic pkt)
        self.assertTrue(captured["sniffer_kwargs"]["lfilter"](reply))

    def test_0402_multiple_replies(self):
        """One device per sniffed reply, order and MACs preserved (cardinality n)."""
        reply1 = make_identify_reply(src="aa:bb:cc:dd:ee:01", name=b"plc-1",
                                     ip="10.0.0.1")
        reply2 = make_identify_reply(src="aa:bb:cc:dd:ee:02", name=b"plc-2",
                                     ip="10.0.0.2")
        devices, _ = self.run_send_identify([reply1, reply2])
        self.assertEqual(len(devices), 2)
        self.assertEqual([d.mac_address for d in devices],
                         ["aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"])
        self.assertEqual([d.name for d in devices], ["plc-1", "plc-2"])
        self.assertEqual([d.ip_address for d in devices], ["10.0.0.1", "10.0.0.2"])

    def test_0403_no_reply_returns_empty_list(self):
        """No sniffed reply -> empty device list (cardinality 0)."""
        devices, captured = self.run_send_identify([])
        self.assertEqual(devices, [])
        self.assertEqual(captured["sendp_calls"], 1) # request still sent

    def test_0404_vlan_encapsulated_reply(self):
        """Replies embedded in 802.1Q frames also get their mac_address."""
        reply = make_identify_reply(src="aa:bb:cc:dd:ee:ff", name=b"plc-vlan",
                                    vlan=True)
        devices, captured = self.run_send_identify([reply])
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].mac_address, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(devices[0].name, "plc-vlan")
        self.assertTrue(captured["sniffer_kwargs"]["lfilter"](reply))

    def test_0405_device_parse_full_packet_directly(self):
        """Non-regression on ProfinetDevice.parse() with a whole packet."""
        reply = make_identify_reply(src="11:22:33:44:55:66", name=b"plc-x",
                                    ip="192.168.1.10")
        device = profinet.ProfinetDevice(reply)
        self.assertEqual(device.mac_address, "11:22:33:44:55:66")
        self.assertEqual(device.name, "plc-x")
        self.assertEqual(device.ip_address, "192.168.1.10")
