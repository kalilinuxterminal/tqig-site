"""Opt-in outbound relay client. The home helper never opens an inbound internet port."""
import asyncio
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from backend.relay_contracts import safe_status


class PhoneChangedError(RuntimeError):
    pass


class RemoteAgent:
    def __init__(self, snapshot, execute, path=None, portal_url=None):
        self.snapshot,self.execute=snapshot,execute
        default_path = Path(__file__).resolve().parents[2]/'.runtime'/'remote-agent.json'
        self.path = Path(path or os.getenv('TQIG_AGENT_STATE_FILE') or default_path)
        self.portal_url=(portal_url or os.getenv('TQIG_PORTAL_URL','http://127.0.0.1:8770')).rstrip('/')
        if not (self.portal_url.startswith('https://') or self.portal_url in {'http://127.0.0.1:8770','http://localhost:8770'}):
            raise ValueError('The account server must use HTTPS or the local preview address.')
        self.credentials=None
        self.task=None
        self.error=None
        self.active=False

    def public(self):
        return {'linked':bool(self.credentials),'running':self.active,'name':self.credentials.get('name') if self.credentials else None,
                'computerId':self.credentials.get('id') if self.credentials else None,'portalUrl':self.portal_url,'error':self.error}

    def request(self,path,body):
        headers={'Content-Type':'application/json'}
        if self.credentials:headers['Authorization']='Bearer '+self.credentials['secret']
        req=urllib.request.Request(self.portal_url+'/api/agent/'+path,data=json.dumps(body).encode(),headers=headers)
        with urllib.request.urlopen(req,timeout=8) as response:return json.load(response)

    def remember_transport(self,device_id,transport):
        if self.credentials and self.credentials['deviceId']==device_id and transport in {'usb','wifi'}:
            self.credentials['transport']=transport
            staged=self.path.with_suffix('.tmp')
            staged.write_text(json.dumps(self.credentials),encoding='utf-8');staged.replace(self.path)

    async def link(self,code,device_id,transport):
        if self.credentials:raise RuntimeError('Unlink the existing remote computer before linking another account.')
        credentials=await asyncio.to_thread(self.request,'enroll',{'code':code})
        # Device identity and the Apple session remain local; the cloud receives neither.
        self.credentials={**credentials,'deviceId':device_id,'transport':transport,'portalUrl':self.portal_url}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(self.credentials),encoding='utf-8')
        self.path.chmod(0o600)
        self.error=None
        self.task=asyncio.create_task(self.run())
        return self.public()

    async def start_existing(self):
        if self.path.exists():
            try:
                data=json.loads(self.path.read_text(encoding='utf-8'))
                if data.get('portalUrl')!=self.portal_url or not all(data.get(k) for k in ['id','secret','deviceId','transport']):raise ValueError()
                self.credentials=data
                self.task=asyncio.create_task(self.run())
            except (ValueError,OSError):self.error='Saved remote authorization is invalid. Unlink and set up again locally.'

    async def run(self):
        failures=0
        self.active=True
        async def heartbeat():
            while self.active:
                await asyncio.sleep(4)
                try:await asyncio.to_thread(self.request,'heartbeat',{'status':safe_status(self.snapshot())})
                except (OSError,ValueError):pass
        keepalive=asyncio.create_task(heartbeat())
        try:
            while self.credentials:
                try:
                    response=await asyncio.to_thread(self.request,'poll',{'status':safe_status(self.snapshot())})
                    failures=0;self.error=None
                    command=response.get('command')
                    if command:
                        result={};error=None
                        try:
                            payload=command['payload']
                            current=self.snapshot()
                            current_phone=current.get('device') or {}
                            # The enrollment authorizes one particular phone, even if a
                            # different phone is connected locally later. Recovery stays available.
                            recovery=command['action'] in {'stop','journey/stop','disconnect'}
                            if not recovery and current.get('connection')=='connected' and current_phone.get('id')!=self.credentials['deviceId']:
                                raise PhoneChangedError()
                            if command['action']=='connect':payload={'id':self.credentials['deviceId'],'transport':self.credentials['transport']}
                            result=await self.execute(command['action'],payload)
                        except PhoneChangedError:
                            error='A different iPhone is connected. Unlink and explicitly link that phone from the home computer.'
                        except Exception:
                            error='The home helper could not complete this action. Check its connection and phone, then retry explicitly.'
                        # No automatic command replay: a lost acknowledgement is an unknown outcome.
                        await asyncio.to_thread(self.request,'result',{'command':command['id'],'result':safe_status(result),'error':error})
                    await asyncio.sleep(2)
                except (OSError,ValueError) as exc:
                    if isinstance(exc,urllib.error.HTTPError) and exc.code==401:
                        try:await self.execute('stop',{})
                        except Exception:pass
                        self.credentials=None;self.path.unlink(missing_ok=True)
                        self.error='Remote authorization was revoked. Normal location was requested locally.'
                        break
                    failures+=1
                    if failures==1:
                        try:await self.execute('journey/pause',{})
                        except Exception:pass
                    self.error='Remote connection interrupted. Reconnecting…'
                    if failures>=5:
                        self.error='Remote control paused after repeated connection failures. Reconnect from the home helper.'
                        try:await self.execute('stop',{})
                        except Exception:pass
                        break
                    await asyncio.sleep(min(2**failures,16))
        except asyncio.CancelledError:raise
        finally:
            self.active=False
            keepalive.cancel()
            try:await keepalive
            except asyncio.CancelledError:pass

    async def close(self,unlink=False):
        if self.task and not self.task.done():
            self.task.cancel()
            try:await self.task
            except asyncio.CancelledError:pass
        if unlink:
            try:await self.execute('stop',{})
            except Exception:pass
            if self.credentials:
                try:await asyncio.to_thread(self.request,'unlink',{})
                except (OSError,ValueError):pass
            self.credentials=None
            self.path.unlink(missing_ok=True)
