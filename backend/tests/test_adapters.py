import unittest
from types import SimpleNamespace
from unittest.mock import patch,AsyncMock
from backend.adapters.wifi import WifiDeviceAdapter
from backend.adapters.browser_usb import BrowserUsbAdapter
from backend.adapters.base import UnavailableTransport

class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_wifi_never_lists_a_cabled_phone_as_wireless(self):
        records=[SimpleNamespace(serial='a',connection_type='USB'),SimpleNamespace(serial='a',connection_type='Network'),SimpleNamespace(serial='b',connection_type='Network')]
        with patch('pymobiledevice3.usbmux.list_devices',new_callable=AsyncMock,return_value=records):
            self.assertEqual(await WifiDeviceAdapter(load_settings=False).discover(),[{'id':'b','transport':'Wi-Fi'}])
    async def test_browser_adapter_is_explicitly_unavailable(self):
        adapter=BrowserUsbAdapter();self.assertFalse(adapter.capabilities()['available'])
        with self.assertRaises(UnavailableTransport):await adapter.discover()
