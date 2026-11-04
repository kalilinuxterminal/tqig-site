"""Bounded IPC proxy for the isolated RemotePairing Wi-Fi worker."""
import asyncio
import json
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

ROOT=Path(__file__).resolve().parents[2]

class WifiLocation:
    def __init__(self,process):self.process=process;self.lock=asyncio.Lock()
    async def call(self,op,**payload):
        async with self.lock:
            self.process.stdin.write((json.dumps({'op':op,**payload})+'\n').encode());await self.process.stdin.drain()
            line=await asyncio.wait_for(self.process.stdout.readline(),60 if op=='open' else 25)
            if not line:raise RuntimeError('The wireless helper stopped. Reconnect your iPhone.')
            result=json.loads(line)
            if not result.get('ok'):raise RuntimeError(result.get('error') or 'Wireless verification did not finish.')
            return result
    async def set(self,lat,lng):await self.call('set',lat=lat,lng=lng)
    async def clear(self):await self.call('clear')
    async def ping(self):await self.call('ping')

@asynccontextmanager
async def open_remote_wifi(device_id):
    runtime=sys.executable
    settings=ROOT/'.runtime'/'wifi-runtime.json'
    if settings.exists():runtime=json.loads(settings.read_text(encoding='utf-8'))['python']
    process=await asyncio.create_subprocess_exec(runtime,'-m','backend.wifi_worker',cwd=str(ROOT),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,creationflags=0x08000000 if os.name=='nt' else 0)
    location=WifiLocation(process)
    try:
        result=await location.call('open',id=device_id)
        if result.get('device',{}).get('id')!=device_id or result['device'].get('transport')!='Wi-Fi':raise RuntimeError('Wireless verification returned the wrong phone or transport.')
        yield location,location.ping,result['device']
    finally:
        if process.returncode is None:
            try:await asyncio.wait_for(location.call('close'),5)
            except Exception:pass
            try:await asyncio.wait_for(process.wait(),5)
            except TimeoutError:process.kill();await process.wait()

async def prepare_remote_pairing(lockdown):
    from pymobiledevice3.remote.tunnel_service import RemotePairingLockdownService
    from pymobiledevice3.exceptions import RemotePairingCompletedError
    service=None
    try:
        service=await RemotePairingLockdownService.create(lockdown)
        try:await asyncio.wait_for(service.connect(autopair=True),15)
        except RemotePairingCompletedError:
            await service.close();service=await RemotePairingLockdownService.create(lockdown)
            await asyncio.wait_for(service.connect(autopair=False),15)
        if not isinstance((service.pair_record or {}).get('peer_alt_irk'),bytes):raise RuntimeError('Wireless pairing did not provide a discovery key. Complete initial USB setup again.')
    finally:
        if service:await service.close()
