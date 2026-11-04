import asyncio
import unittest
from backend.main import create_app
from backend.services.device_controller import DeviceController
from backend.tests.test_lifecycle import TestDevice, discovery
import httpx

class APITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.device=TestDevice();self.controller=DeviceController(self.device.open,discovery)
        self.app=create_app(self.controller)
        self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),base_url='http://127.0.0.1:8766')
        token=(await self.client.get('/api/session')).json()['token']
        self.headers={'Origin':'http://127.0.0.1:8766','X-TQIG-Token':token}
    async def asyncTearDown(self):await self.controller.close();await self.client.aclose()
    async def test_origin_host_and_token_boundary(self):
        self.assertEqual((await self.client.get('/api/status')).status_code,403)
        self.assertEqual((await self.client.get('/api/status',headers={**self.headers,'Origin':'https://evil.test'})).status_code,403)
        self.assertEqual((await self.client.get('/api/session',headers={'Origin':'https://tqig.space'})).status_code,403)
        self.assertEqual((await self.client.get('/api/status',headers={**self.headers,'Host':'rebind.test:8766'})).status_code,403)
    async def test_cloud_origin_requires_explicit_local_code(self):
        r=await self.client.get('/api/status',headers={**self.headers,'Origin':'https://tqig.space'})
        self.assertEqual(r.status_code,200);self.assertEqual(r.headers['access-control-allow-origin'],'https://tqig.space')
    async def test_set_stop_and_state_contract(self):
        r=await self.client.post('/api/connect',headers=self.headers,json={'id':'test-usb','transport':'usb'})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['state'],'ready')
        r=await self.client.post('/api/location',headers=self.headers,json={'lat':40.7,'lng':-74.})
        self.assertEqual(r.json()['state'],'active');self.assertIsNone(r.json()['observedCoordinates'])
        r=await self.client.post('/api/stop',headers=self.headers,json={})
        self.assertEqual(r.json()['state'],'ready');self.assertEqual(r.json()['simulation'],'clear_sent')
        self.assertFalse(r.json()['portableAvailable'])
    async def test_invalid_coordinates_and_route_rejected(self):
        for payload in [{'lat':True,'lng':0},{'lat':91,'lng':0},{'lat':0,'lng':0,'command':'bad'}]:
            r=await self.client.post('/api/location',headers=self.headers,json=payload);self.assertEqual(r.status_code,422)
        r=await self.client.post('/api/journey/start',headers=self.headers,json={'frames':[]})
        self.assertEqual(r.status_code,422);self.assertEqual(self.device.calls,[])

    async def test_browser_cannot_enable_cabled_lan_diagnostic_mode(self):
        r=await self.client.post('/api/connect',headers=self.headers,json={'id':'test-usb','transport':'wifi','lanDiagnostic':True})
        self.assertEqual(r.status_code,422);self.assertEqual(self.device.calls,[])
    async def test_refresh_routes_have_spa_fallback(self):
        r=await self.client.get('/app/drive');self.assertEqual(r.status_code,200);self.assertIn('TQIG',r.text)
    async def test_wifi_setup_requires_explicit_confirm_and_verified_usb(self):
        r=await self.client.post('/api/wifi/setup',headers=self.headers,json={'confirm':False})
        self.assertEqual(r.status_code,422)
        r=await self.client.post('/api/wifi/setup',headers=self.headers,json={'confirm':True})
        self.assertEqual(r.status_code,409)
    async def test_wifi_setup_calls_only_the_targeted_setup_adapter(self):
        from unittest.mock import AsyncMock,patch
        await self.client.post('/api/connect',headers=self.headers,json={'id':'test-usb'})
        self.controller.device['transport']='USB'
        with patch('backend.main.enable_wifi',new_callable=AsyncMock) as setup:
            setup.return_value={'enabled':True,'verifiedNetworkSession':False}
            r=await self.client.post('/api/wifi/setup',headers=self.headers,json={'confirm':True})
            self.assertEqual(r.status_code,200);setup.assert_awaited_once_with('test-usb')
            self.assertFalse(r.json()['wifiSetup']['verifiedNetworkSession'])

class WebSocketTests(unittest.TestCase):
    def test_websocket_authentication_and_status(self):
        from starlette.testclient import TestClient
        device=TestDevice();controller=DeviceController(device.open,discovery)
        with TestClient(create_app(controller),base_url='http://127.0.0.1:8766') as client:
            token=client.get('/api/session').json()['token']
            with client.websocket_connect('ws://127.0.0.1:8766/api/events',headers={'Origin':'http://127.0.0.1:8766','Host':'127.0.0.1:8766'}) as ws:
                ws.send_json({'token':token});data=ws.receive_json();self.assertEqual(data['state'],'disconnected')
