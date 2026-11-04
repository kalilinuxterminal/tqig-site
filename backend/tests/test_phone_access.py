import asyncio
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,AsyncMock
from fastapi.testclient import TestClient
from backend.accounts import Store
from backend.portal import create_portal
from backend.services.phone_access import PhoneAccess
from backend.tests import test_api as fixture

ORIGIN='https://test-home-phone-access.trycloudflare.com'

class FakeProcess:
    def __init__(self):
        self.returncode=None;self.done=asyncio.Event();self.stdout=self;self.sent=0
    async def readline(self):
        if self.sent==0:self.sent=1;return (ORIGIN+'\n').encode()
        if self.sent==1:self.sent=2;return b'INF Registered tunnel connection\n'
        await self.done.wait();return b''
    def terminate(self):self.returncode=0;self.done.set()
    def kill(self):self.terminate()
    async def wait(self):await self.done.wait();return self.returncode

class FakeServer:
    def __init__(self,config):self.started=False;self.should_exit=False
    async def serve(self):
        self.started=True
        while not self.should_exit:await asyncio.sleep(.01)

class ManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_verified_component_tunnels_only_the_account_listener_and_stops_cleanly(self):
        with tempfile.TemporaryDirectory() as folder:
            binary=Path(folder)/'client.exe';binary.write_bytes(b'fixture')
            factory_origins=[]
            def factory(origin):factory_origins.append(origin);return object()
            manager=PhoneAccess(factory,lambda:True,binary)
            with patch('backend.services.phone_access.SHA256',hashlib.sha256(b'fixture').hexdigest()),patch('backend.services.phone_access.asyncio.create_subprocess_exec',new_callable=AsyncMock,return_value=FakeProcess()) as spawn,patch('backend.services.phone_access.PhoneServer',FakeServer),patch.object(manager,'_wait_public',new_callable=AsyncMock):
                try:
                    result=await manager.start()
                    self.assertEqual(result['state'],'ready');self.assertEqual(result['url'],ORIGIN)
                    self.assertEqual(factory_origins,[ORIGIN])
                    args=spawn.call_args.args
                    self.assertIn('http://127.0.0.1:8772',args)
                    self.assertNotIn('http://127.0.0.1:8766',args)
                    self.assertEqual((await manager.start())['state'],'ready');spawn.assert_awaited_once()
                finally:await manager.stop()
                self.assertEqual(manager.status()['state'],'off');self.assertIsNone(manager.status()['url'])

    async def test_owner_and_checksum_are_required_before_starting_a_process(self):
        with tempfile.TemporaryDirectory() as folder:
            binary=Path(folder)/'client.exe';binary.write_bytes(b'unverified')
            with patch('backend.services.phone_access.asyncio.create_subprocess_exec',new_callable=AsyncMock) as spawn:
                with self.assertRaisesRegex(RuntimeError,'owner'):await PhoneAccess(lambda _:None,lambda:False,binary).start()
                with self.assertRaisesRegex(RuntimeError,'verification'):await PhoneAccess(lambda _:None,lambda:True,binary).start()
                spawn.assert_not_awaited()

    async def test_failed_public_health_never_reports_a_ready_link(self):
        with tempfile.TemporaryDirectory() as folder:
            binary=Path(folder)/'client.exe';binary.write_bytes(b'fixture')
            manager=PhoneAccess(lambda _:object(),lambda:True,binary)
            with patch('backend.services.phone_access.SHA256',hashlib.sha256(b'fixture').hexdigest()),patch('backend.services.phone_access.asyncio.create_subprocess_exec',new_callable=AsyncMock,return_value=FakeProcess()),patch('backend.services.phone_access.PhoneServer',FakeServer),patch.object(manager,'_wait_public',new_callable=AsyncMock,side_effect=RuntimeError('Public address unavailable')):
                with self.assertRaisesRegex(RuntimeError,'Public address'):await manager.start()
            status=manager.status()
            self.assertEqual(status['state'],'off');self.assertIsNone(status['url']);self.assertIsNotNone(status['error'])

class PhoneAccessAPITests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=fixture.APITests.asyncSetUp
    asyncTearDown=fixture.APITests.asyncTearDown

    async def test_temporary_owner_password_blocks_opening_the_link(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder)/'portal.sqlite3')
            store.create_user('test@example.test','Test Owner','A-long-fixture-password-745!',owner=True)
            store.configure_owner_login('admin','admin')
            with patch('backend.portal.DATA',Path(folder)), patch('backend.services.phone_access.asyncio.create_subprocess_exec',new_callable=AsyncMock) as spawn:
                response = await self.client.post('/api/phone-access/start',headers=self.headers,json={'confirm':True})
                self.assertEqual(response.status_code,409)
                self.assertIn('Change the temporary owner password',response.json()['detail'])
                self.assertEqual(self.app.state.phone_access.status()['state'],'off')
                spawn.assert_not_awaited()

    async def test_start_needs_explicit_local_authorization_and_confirmation(self):
        manager=self.app.state.phone_access
        with patch.object(manager,'start',new_callable=AsyncMock,return_value={'state':'ready'}) as start:
            self.assertEqual((await self.client.post('/api/phone-access/start',json={'confirm':True})).status_code,403)
            self.assertEqual((await self.client.post('/api/phone-access/start',headers={**self.headers,'Origin':'https://tqig.space'},json={'confirm':True})).status_code,403)
            self.assertEqual((await self.client.post('/api/phone-access/start',headers=self.headers,json={'confirm':False})).status_code,422)
            start.assert_not_awaited()
            self.assertEqual((await self.client.post('/api/phone-access/start',headers=self.headers,json={'confirm':True})).status_code,200)
            start.assert_awaited_once()

    async def test_stop_and_status_require_the_local_helper_boundary(self):
        self.assertEqual((await self.client.get('/api/phone-access')).status_code,403)
        result=await self.client.get('/api/phone-access',headers=self.headers)
        self.assertEqual(result.json()['target'],'account-dashboard-only')
        self.assertEqual((await self.client.post('/api/phone-access/stop',headers={**self.headers,'Origin':'https://tqig.space'},json={})).status_code,403)
        self.assertEqual((await self.client.post('/api/phone-access/stop',headers=self.headers,json={})).status_code,200)

class PublicPortalTests(unittest.TestCase):
    def test_legacy_short_password_is_accepted_locally_but_rejected_remotely(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder)/'test.db'
            local = create_portal(db,True)
            local.state.store.create_user('test@example.test','Test Owner','A-long-fixture-password-745!',owner=True)
            local.state.store.configure_owner_login('admin','admin')
            body = {'email':'admin','password':'admin'}
            local_origin = 'http://127.0.0.1:8770'
            with TestClient(local,base_url=local_origin,headers={'Origin':local_origin}) as client:
                self.assertEqual(client.post('/api/auth/signin',json=body).status_code,200)
            public = create_portal(db,False,public_origin=ORIGIN)
            with TestClient(public,base_url=ORIGIN,headers={'Origin':ORIGIN}) as client:
                response = client.post('/api/auth/signin',json=body)
                self.assertEqual(response.status_code,401)
                self.assertNotIn('set-cookie',response.headers)

    def test_public_access_keeps_owner_setup_closed_and_local_device_apis_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            app=create_portal(Path(folder)/'test.db',False,public_origin=ORIGIN)
            with TestClient(app,base_url=ORIGIN,headers={'Origin':ORIGIN}) as client:
                self.assertFalse(client.get('/api/auth/setup').json()['allowed'])
                self.assertEqual(client.get('/api/admin/users').status_code,401)
                self.assertEqual(client.get('/api/computers').status_code,401)
                for path in ['/api/session','/api/status','/api/phone-access','/api/diagnostics']:
                    self.assertEqual(client.get(path).status_code,404)
                self.assertEqual(client.get('/api/auth/session',headers={'Host':'other.trycloudflare.com'}).status_code,403)

    def test_public_signin_uses_secure_cookie_with_existing_account(self):
        with tempfile.TemporaryDirectory() as folder:
            app=create_portal(Path(folder)/'test.db',False,public_origin=ORIGIN)
            app.state.store.create_user('test@example.test','Test Owner','A-long-fixture-password-745!',owner=True)
            with TestClient(app,base_url=ORIGIN,headers={'Origin':ORIGIN}) as client:
                result=client.post('/api/auth/signin',json={'email':'test@example.test','password':'A-long-fixture-password-745!','remember':True})
                self.assertEqual(result.status_code,200)
                cookie=result.headers['set-cookie']
                for token in ['__Host-tqig_session','HttpOnly','Secure','SameSite=lax','Max-Age=2592000']:self.assertIn(token,cookie)
                self.assertEqual(client.get('/api/auth/session').json()['user']['role'],'owner')
