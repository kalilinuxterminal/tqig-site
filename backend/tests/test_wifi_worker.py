import asyncio
import json
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,AsyncMock
from backend.adapters.wifi_remote import WifiLocation,open_remote_wifi
from backend.adapters.wifi import WifiDeviceAdapter
from backend.services.remote_agent import RemoteAgent
from backend.wifi_worker import lan
from types import SimpleNamespace

class Pipe:
    def __init__(self,responses):self.responses=list(responses);self.writes=[]
    def write(self,value):self.writes.append(json.loads(value))
    async def drain(self):pass
    async def readline(self):return (json.dumps(self.responses.pop(0))+'\n').encode() if self.responses else b''
class Process:
    def __init__(self,responses):self.stdin=Pipe([]);self.stdout=Pipe(responses);self.returncode=None;self.killed=False
    async def wait(self):self.returncode=0;return 0
    def kill(self):self.killed=True;self.returncode=-1

class WifiWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_ipc_sends_only_coordinate_operations_and_checks_replies(self):
        process=Process([{'ok':True},{'ok':True},{'ok':False,'error':'Phone unavailable'}]);proxy=WifiLocation(process)
        await proxy.set(28.5550254,-81.7661906);await proxy.clear()
        self.assertEqual(process.stdin.writes,[{'op':'set','lat':28.5550254,'lng':-81.7661906},{'op':'clear'}])
        with self.assertRaisesRegex(RuntimeError,'unavailable'):await proxy.ping()

    async def test_worker_start_rejects_wrong_identity_and_closes(self):
        process=Process([{'ok':True,'device':{'id':'other','transport':'Wi-Fi'}},{'ok':True}])
        with tempfile.TemporaryDirectory() as folder,patch('backend.adapters.wifi_remote.ROOT',Path(folder)),patch('backend.adapters.wifi_remote.asyncio.create_subprocess_exec',new_callable=AsyncMock,return_value=process) as spawn:
            with self.assertRaisesRegex(RuntimeError,'wrong phone'):
                async with open_remote_wifi('authorized'):pass
            self.assertEqual(process.stdin.writes[0],{'op':'open','id':'authorized'})
            self.assertEqual(process.stdin.writes[-1],{'op':'close'})
            self.assertNotIn('shell',spawn.call_args.kwargs)

    async def test_verified_worker_preserves_network_transport(self):
        process=Process([{'ok':True,'device':{'id':'authorized','transport':'Wi-Fi'}},{'ok':True}])
        with tempfile.TemporaryDirectory() as folder,patch('backend.adapters.wifi_remote.ROOT',Path(folder)),patch('backend.adapters.wifi_remote.asyncio.create_subprocess_exec',new_callable=AsyncMock,return_value=process):
            async with open_remote_wifi('authorized') as (_,_,metadata):self.assertEqual(metadata['transport'],'Wi-Fi')
        self.assertEqual(process.returncode,0)

    async def test_empty_worker_reply_cannot_claim_success(self):
        with self.assertRaisesRegex(RuntimeError,'stopped'):await WifiLocation(Process([])).ping()

    async def test_only_private_ipv4_is_eligible_for_explicit_lan_transport(self):
        self.assertTrue(lan('192.168.1.50'))
        for host in ['127.0.0.1','0.0.0.0','169.254.1.1','8.8.8.8','::1','example.com']:self.assertFalse(lan(host))

    async def test_normal_worker_open_rejects_a_cabled_phone_before_network_startup(self):
        from backend.wifi_worker import main
        request=io.StringIO(json.dumps({'op':'open','id':'authorized'})+'\n')
        with patch('backend.wifi_worker.sys.stdin',request),patch('pymobiledevice3.usbmux.list_devices',new_callable=AsyncMock,return_value=[SimpleNamespace(serial='authorized',connection_type='USB')]),patch('backend.wifi_worker.network_rsd') as network:
            with self.assertRaisesRegex(RuntimeError,'Unplug USB'):await main()
            network.assert_not_called()

    async def test_remembered_target_and_transport_cannot_switch_bound_phone(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'address.json';adapter=WifiDeviceAdapter(load_settings=False,path=path);adapter.remember_device('authorized')
            self.assertEqual(WifiDeviceAdapter(path=path).target_id,'authorized')
            agent=RemoteAgent(lambda:{},AsyncMock(),path=Path(folder)/'agent.json')
            agent.credentials={'deviceId':'authorized','transport':'usb','secret':'fixture'}
            agent.remember_transport('different','wifi');self.assertEqual(agent.credentials['transport'],'usb')
            agent.remember_transport('authorized','wifi')
            self.assertEqual(json.loads(agent.path.read_text())['transport'],'wifi')
