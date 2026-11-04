"""Temporary authenticated dashboard access. Only the account service is tunneled, never the Apple helper."""
import asyncio
import hashlib
import os
import re
import json
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path
import uvicorn
from backend.install_phone_access import BINARY,SHA256

PUBLIC_PORT=8772
URL_PATTERN=re.compile(r'https://[a-z0-9]+(?:-[a-z0-9]+){2,6}\.trycloudflare\.com\b')

class PhoneServer(uvicorn.Server):
    @contextmanager
    def capture_signals(self):yield
    async def startup(self,sockets=None):
        try:await super().startup(sockets)
        except SystemExit:raise RuntimeError('The phone-access listener is already in use.') from None

class PhoneAccess:
    def __init__(self,factory,owner_ready,binary=BINARY):
        self.factory,self.owner_ready,self.binary=factory,owner_ready,Path(binary)
        self.process=None;self.server=None;self.server_task=None;self.log_task=None
        self.url=None;self.error=None;self.starting=False;self.edge_connected=False;self.public_verified=False;self.lock=asyncio.Lock()
        self.debug_events=[]

    def status(self):
        alive=self.process is not None and self.process.returncode is None
        ready=bool(alive and self.edge_connected and self.public_verified and self.server and self.server.started and self.url and self.server_task and not self.server_task.done())
        return {'state':'starting' if self.starting else 'ready' if ready else 'off',
                'url':self.url if ready else None,'temporary':True,'error':self.error,
                'componentInstalled':self.binary.exists(),'target':'account-dashboard-only'}

    async def start(self):
        async with self.lock:
            if self.status()['state']=='ready':return self.status()
            if not await asyncio.to_thread(self.owner_ready):
                raise RuntimeError('Create your owner account locally before enabling phone access.')
            if not self.binary.exists():raise RuntimeError('The phone-access component is missing. Run the phone-access setup included with TQIG.')
            actual=await asyncio.to_thread(lambda:hashlib.sha256(self.binary.read_bytes()).hexdigest())
            if actual!=SHA256:raise RuntimeError('The phone-access component failed verification. Run its setup again.')
            await self.close(clear_error=False)
            self.starting=True;self.error=None
            announced=asyncio.get_running_loop().create_future()
            try:
                self.process=await asyncio.create_subprocess_exec(str(self.binary),'tunnel','--no-autoupdate','--url',f'http://127.0.0.1:{PUBLIC_PORT}',
                    '--protocol','http2','--metrics','127.0.0.1:0',stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT,
                    creationflags=0x08000000 if os.name=='nt' else 0)
                async def read_log():
                    while line:=await self.process.stdout.readline():
                        decoded=line.decode(errors='replace')
                        if 'Registered tunnel connection' in decoded:self.edge_connected=True
                        if 'ERR' in decoded or 'WRN' in decoded:
                            sanitized=re.sub(r'https?://\S+','[address]',decoded.strip())
                            sanitized=re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b','[network]',sanitized)
                            sanitized=re.sub(r'\b[0-9a-f]{8}-[0-9a-f-]{27,}\b','[identifier]',sanitized)
                            self.debug_events=(self.debug_events+[sanitized])[-8:]
                        match=URL_PATTERN.search(decoded)
                        if match and not announced.done():announced.set_result(match.group())
                    if not announced.done():announced.set_exception(RuntimeError('The secure link could not start. Check the computer’s internet connection.'))
                self.log_task=asyncio.create_task(read_log())
                self.url=await asyncio.wait_for(announced,40)
                self.server=PhoneServer(uvicorn.Config(self.factory(self.url),host='127.0.0.1',port=PUBLIC_PORT,access_log=False,log_level='warning'))
                self.server_task=asyncio.create_task(self.server.serve())
                for _ in range(400):
                    if self.server.started and self.edge_connected:break
                    if self.server_task.done():raise RuntimeError('The account dashboard could not start its phone-access listener.')
                    await asyncio.sleep(.05)
                if not self.server.started or not self.edge_connected:raise RuntimeError('The secure tunnel could not connect to its internet service. Phone access is not ready.')
                await self._wait_public()
                self.public_verified=True
                self.starting=False
                return self.status()
            except BaseException:
                self.error='Phone access did not finish starting. Check the PC’s internet connection and try again.'
                await self.close(clear_error=False)
                raise
            finally:self.starting=False

    async def close(self,clear_error=True):
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:await asyncio.wait_for(self.process.wait(),5)
            except TimeoutError:self.process.kill();await self.process.wait()
        if self.log_task:
            self.log_task.cancel()
            await asyncio.gather(self.log_task,return_exceptions=True)
        if self.server:
            self.server.should_exit=True
            if self.server_task:
                try:await asyncio.wait_for(self.server_task,5)
                except TimeoutError:self.server_task.cancel();await asyncio.gather(self.server_task,return_exceptions=True)
                except Exception:pass
        self.process=None;self.server=None;self.server_task=None;self.log_task=None;self.url=None;self.edge_connected=False;self.public_verified=False
        if clear_error:self.error=None

    async def stop(self):
        async with self.lock:await self.close()

    async def _wait_public(self):
        def healthy():
            with urllib.request.urlopen(self.url+'/api/portal/health',timeout=6) as response:
                data=json.load(response)
                return data.get('service')=='TQIG accounts and remote relay' and data.get('localPreview') is False
        deadline=time.monotonic()+65
        while time.monotonic()<deadline:
            try:
                if await asyncio.to_thread(healthy):return
            except (OSError,ValueError):pass
            if self.process.returncode is not None:break
            await asyncio.sleep(2)
        raise RuntimeError('The temporary internet address could not be verified yet. Wait a moment and retry phone access.')
