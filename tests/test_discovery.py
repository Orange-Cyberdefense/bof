"""unittest for multicast discovery ``bof.modules.discovery``

- multicast_discovery forwards the right keyword arguments to each protocol
  discovery function (Profinet: iface + mac_addr, KNX: ip).
- LLDP sniffing is started/stopped around the multicast requests.
- An OSError raised by one protocol discovery is skipped without breaking
  the other protocols.

All network-touching dependencies are mocked (profinet_discovery,
knx_discovery, lldp.start_listening/stop_listening, sleep), so no root
privileges or network access are needed.
"""

import unittest
from unittest.mock import patch

from bof import DEFAULT_IFACE
from bof.layers import knx, lldp, profinet
from bof.modules import discovery

KNX_CUSTOM = "224.0.23.99"
PNDCP_CUSTOM = "01:0e:cf:00:00:01"


class Test01MulticastDiscoveryKwargs(unittest.TestCase):
    """multicast_discovery must forward multicast addresses as proper kwargs."""

    def _run_discovery(self, **kwargs):
        """Run multicast_discovery with all network parts mocked out."""
        with patch("bof.modules.discovery.profinet_discovery") as mock_pndcp, \
             patch("bof.modules.discovery.knx_discovery") as mock_knx, \
             patch("bof.modules.discovery.lldp.start_listening") as mock_start, \
             patch("bof.modules.discovery.lldp.stop_listening") as mock_stop, \
             patch("bof.modules.discovery.sleep") as mock_sleep:
            mock_pndcp.return_value = []
            mock_knx.return_value = []
            mock_start.return_value = "sniffer"
            mock_stop.return_value = []
            result = discovery.multicast_discovery(**kwargs)
        return result, mock_pndcp, mock_knx, mock_start, mock_stop, mock_sleep

    def test_0101_custom_addresses_forwarded(self):
        """knx_multicast -> knx_discovery(ip=...), pndcp_multicast -> mac_addr."""
        _, mock_pndcp, mock_knx, _, _, _ = self._run_discovery(
            knx_multicast=KNX_CUSTOM, pndcp_multicast=PNDCP_CUSTOM)
        # exact kwargs: mac_addr/iface must NOT leak into knx_discovery
        mock_knx.assert_called_once_with(ip=KNX_CUSTOM)
        mock_pndcp.assert_called_once_with(iface=DEFAULT_IFACE,
                                           mac_addr=PNDCP_CUSTOM)

    def test_0102_default_addresses_forwarded(self):
        """Defaults: knx ip=224.0.23.12, pndcp mac_addr=01:0e:cf:00:00:00."""
        _, mock_pndcp, mock_knx, _, _, _ = self._run_discovery()
        mock_knx.assert_called_once_with(ip="224.0.23.12")
        mock_pndcp.assert_called_once_with(iface=DEFAULT_IFACE,
                                           mac_addr="01:0e:cf:00:00:00")
        # sanity check: those literals are the layer default constants
        self.assertEqual(knx.MULTICAST_ADDR, "224.0.23.12")
        self.assertEqual(profinet.MULTICAST_MAC, "01:0e:cf:00:00:00")

    def test_0103_custom_iface_forwarded(self):
        """iface goes to profinet_discovery and to the LLDP sniffer."""
        _, mock_pndcp, mock_knx, mock_start, _, _ = self._run_discovery(
            iface="eth1", knx_multicast=KNX_CUSTOM, pndcp_multicast=PNDCP_CUSTOM)
        mock_pndcp.assert_called_once_with(iface="eth1", mac_addr=PNDCP_CUSTOM)
        mock_knx.assert_called_once_with(ip=KNX_CUSTOM)
        mock_start.assert_called_once_with("eth1")


class Test02MulticastDiscoveryFlow(unittest.TestCase):
    """Sniffing lifecycle, result aggregation and error handling."""

    def test_0201_devices_aggregated_sniffer_stopped(self):
        """Devices from all protocols are returned; sniffer is stopped."""
        with patch("bof.modules.discovery.profinet_discovery") as mock_pndcp, \
             patch("bof.modules.discovery.knx_discovery") as mock_knx, \
             patch("bof.modules.discovery.lldp.start_listening") as mock_start, \
             patch("bof.modules.discovery.lldp.stop_listening") as mock_stop, \
             patch("bof.modules.discovery.sleep") as mock_sleep:
            mock_pndcp.return_value = ["pn_dev"]
            mock_knx.return_value = ["knx_dev"]
            mock_start.return_value = "sniffer"
            mock_stop.return_value = []
            result = discovery.multicast_discovery()
            self.assertEqual(result, ["pn_dev", "knx_dev"])
            mock_start.assert_called_once_with(DEFAULT_IFACE)
            mock_stop.assert_called_once_with("sniffer")
            mock_sleep.assert_called_once_with(
                lldp.LLDP_DEFAULT_TIMEOUT - profinet.DEFAULT_TIMEOUT)

    def test_0202_oserror_skips_one_protocol(self):
        """OSError from knx_discovery does not prevent profinet results."""
        with patch("bof.modules.discovery.profinet_discovery") as mock_pndcp, \
             patch("bof.modules.discovery.knx_discovery") as mock_knx, \
             patch("bof.modules.discovery.lldp.start_listening") as mock_start, \
             patch("bof.modules.discovery.lldp.stop_listening") as mock_stop, \
             patch("bof.modules.discovery.sleep"):
            mock_pndcp.return_value = ["pn_dev"]
            mock_knx.side_effect = OSError("no route")
            mock_start.return_value = "sniffer"
            mock_stop.return_value = []
            result = discovery.multicast_discovery()
            self.assertEqual(result, ["pn_dev"])
            mock_pndcp.assert_called_once()
            mock_knx.assert_called_once_with(ip="224.0.23.12")

    def test_0203_all_protocols_oserror_returns_empty(self):
        """OSError from every multicast protocol still returns a list."""
        with patch("bof.modules.discovery.profinet_discovery") as mock_pndcp, \
             patch("bof.modules.discovery.knx_discovery") as mock_knx, \
             patch("bof.modules.discovery.lldp.start_listening") as mock_start, \
             patch("bof.modules.discovery.lldp.stop_listening") as mock_stop, \
             patch("bof.modules.discovery.sleep"):
            mock_pndcp.side_effect = OSError("down")
            mock_knx.side_effect = OSError("down")
            mock_start.return_value = "sniffer"
            mock_stop.return_value = []
            result = discovery.multicast_discovery()
            self.assertEqual(result, [])

    def test_0204_verbose_prints_multicast_addresses(self):
        """The vprint output still shows the multicast addresses used."""
        with patch("bof.modules.discovery.profinet_discovery") as mock_pndcp, \
             patch("bof.modules.discovery.knx_discovery") as mock_knx, \
             patch("bof.modules.discovery.lldp.start_listening") as mock_start, \
             patch("bof.modules.discovery.lldp.stop_listening") as mock_stop, \
             patch("bof.modules.discovery.sleep"), \
             patch("builtins.print") as mock_print:
            mock_pndcp.return_value = []
            mock_knx.return_value = []
            mock_start.return_value = "sniffer"
            mock_stop.return_value = []
            discovery.multicast_discovery(knx_multicast=KNX_CUSTOM,
                                          pndcp_multicast=PNDCP_CUSTOM,
                                          verbose=True)
            printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list
                               if c.args)
            self.assertIn(KNX_CUSTOM, printed)
            self.assertIn(PNDCP_CUSTOM, printed)


if __name__ == "__main__":
    unittest.main()
