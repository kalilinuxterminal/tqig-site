import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from backend.adapters.wifi import WifiDeviceAdapter
from backend.adapters.wifi_tcp import trusted_tcp


class WifiAddressTests(unittest.TestCase):
    def test_private_address_settings_are_local_and_public_loopback_addresses_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter=WifiDeviceAdapter(load_settings=False,path=Path(folder)/'wifi.json')
            for address in ['127.0.0.1','0.0.0.0','8.8.8.8','https://example.test']:
                with self.assertRaises(ValueError):adapter.configure('fixture-device',address)
            adapter.configure('fixture-device','192.168.10.25')
            self.assertEqual(adapter.manual['id'],'fixture-device')
            self.assertNotIn('192.168.10.25',str(adapter.capabilities()))


class WifiTrustTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_pair_record_never_attempts_new_wireless_pairing(self):
        with patch('backend.adapters.wifi_tcp.get_usbmux_pairing_record',new_callable=AsyncMock,return_value=None),patch('backend.adapters.wifi_tcp.create_using_tcp',new_callable=AsyncMock) as create:
            with self.assertRaises(RuntimeError):await trusted_tcp('192.168.10.25','fixture-device')
            create.assert_not_called()

    async def test_wrong_device_identity_is_closed_instead_of_reported_connected(self):
        client=SimpleNamespace(paired=True,udid='other-device',close=AsyncMock())
        with patch('backend.adapters.wifi_tcp.get_usbmux_pairing_record',new_callable=AsyncMock,return_value={'fixture':True}),patch('backend.adapters.wifi_tcp.create_using_tcp',new_callable=AsyncMock,return_value=client) as create:
            with self.assertRaises(RuntimeError):await trusted_tcp('192.168.10.25','fixture-device')
            client.close.assert_awaited_once()
            self.assertFalse(create.call_args.kwargs['autopair'])
