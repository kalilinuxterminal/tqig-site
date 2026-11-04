import asyncio
import json
import logging
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.adapters.local_bridge import LocalBridgeAdapter, enable_wifi
from backend.adapters.wifi import WifiDeviceAdapter
from backend.adapters.browser_usb import BrowserUsbAdapter
from backend.contracts import ConnectBody, Coordinates, RouteBody, PortableObservation, WifiSetup, RemoteLink, WifiAddress
from backend.services.device_controller import DeviceController
from backend.services.playback import PlaybackController
from backend.services.remote_agent import RemoteAgent
from backend.services.connection_health import connection_health,connection_error
from backend.services.phone_access import PhoneAccess

PORT = 8766
LOCAL = {f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}'}
ORIGINS = LOCAL | {'https://tqig.space', 'http://127.0.0.1:5174', 'http://localhost:5174','http://127.0.0.1:8770','http://localhost:8770'}
HOSTS = {f'127.0.0.1:{PORT}', f'localhost:{PORT}'}
DIST = Path(__file__).resolve().parents[1] / 'dist'
logger = logging.getLogger('tqig')

def create_app(device=None):
    injected = device is not None
    adapters = {a.id:a for a in [LocalBridgeAdapter(), WifiDeviceAdapter(load_settings=not injected), BrowserUsbAdapter()]}
    usb = adapters['usb']
    device = device or DeviceController(usb.open, usb.discover)
    usb.on_phase=lambda phase:setattr(device,'state',phase)
    playback = PlaybackController(device)
    mutation = asyncio.Lock()
    token = secrets.token_urlsafe(32)
    recent = defaultdict(deque)
    portable_observation = None
    remote = None
    def public_portal(origin):
        from backend.portal import create_portal
        return create_portal(local_preview=False,public_origin=origin)
    def owner_ready():
        from backend.portal import DATA
        from backend.accounts import Store
        store = Store(DATA/'portal.sqlite3')
        if store.owner_uses_temporary_password():
            raise RuntimeError('Change the temporary owner password in Account & security on this computer before enabling phone access.')
        return store.has_owner()
    phone_access=PhoneAccess(public_portal,owner_ready)

    def snapshot():
        return {**device.snapshot(), 'journey': playback.snapshot(),
                'capabilities': {k:a.capabilities() for k,a in adapters.items()},
                'portableObservation': portable_observation, 'portableAvailable': False,
                'remoteControl':remote.public() if remote else None,
                'helperVersion': '0.9.0', 'serverTime': time.time()}

    @asynccontextmanager
    async def lifespan(app):
        if not injected: await remote.start_existing()
        yield
        await phone_access.close()
        await remote.close()
        await playback.stop(clear=False)
        await device.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.phone_access=phone_access
    app.add_middleware(CORSMiddleware, allow_origins=list(ORIGINS), allow_credentials=False,
                       allow_methods=['GET','POST','OPTIONS'], allow_headers=['Content-Type','X-TQIG-Token'], max_age=300)

    @app.middleware('http')
    async def guard(request: Request, call_next):
        host, origin = request.headers.get('host',''), request.headers.get('origin')
        if host not in HOSTS or origin and origin not in ORIGINS:
            return JSONResponse({'detail':'Open TQIG from its trusted website or this local helper.'},403)
        path = request.url.path
        local_origin = origin in LOCAL or not origin and request.headers.get('sec-fetch-site') in {None,'none','same-origin'}
        local_document=path in {'/authorize','/recovery'} and request.method=='GET' and request.headers.get('sec-fetch-mode')=='navigate'
        if path in {'/api/session','/authorize','/recovery'} and not (local_origin or local_document):
            return JSONResponse({'detail':'Open the helper page locally to authorize this browser.'},403)
        if path.startswith('/api/') and path not in {'/api/session','/api/health'} and request.method!='OPTIONS':
            if not secrets.compare_digest(request.headers.get('x-tqig-token',''),token):
                return JSONResponse({'detail':'Authorize this browser with your local helper code.'},403)
        if request.method=='POST':
            if origin not in ORIGINS:
                return JSONResponse({'detail':'An authorized browser origin is required.'},403)
            if request.headers.get('content-type','').split(';')[0]!='application/json':
                return JSONResponse({'detail':'JSON request required.'},415)
            body = await request.body()
            if len(body)>5_000_000:
                return JSONResponse({'detail':'Request exceeds the journey size limit.'},413)
            now=time.monotonic(); queue=recent[path]
            while queue and queue[0]<now-60: queue.popleft()
            if len(queue)>=60:
                return JSONResponse({'detail':'Too many requests. Wait a moment and retry.'},429)
            queue.append(now)
        response=await call_next(request)
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY',
                                 'Referrer-Policy':'no-referrer','Content-Security-Policy':"frame-ancestors 'none'; object-src 'none'; base-uri 'self'"})
        return response

    async def perform(fn):
        if mutation.locked():
            raise HTTPException(409,'Another device action is finishing. Wait before trying again.')
        async with mutation:
            try:
                result=await fn()
                logger.info(json.dumps({'event':'device_action','result':'completed','state':device.state}))
                return result
            except Exception as exc:
                logger.warning(json.dumps({'event':'device_action','result':'failed','errorType':type(exc).__name__}))
                raise HTTPException(409,connection_error(exc)) from exc

    @app.get('/api/health')
    async def health():
        return {'service':'TQIG local device helper','version':'0.9.0','localOnly':True}

    @app.get('/api/session')
    async def session():
        return {'token':token}

    @app.get('/api/diagnostics')
    async def diagnostics():
        return await connection_health(adapters['usb'].discover, bool(adapters['wifi'].manual))

    @app.get('/api/phone-access')
    async def phone_access_status():return phone_access.status()

    @app.post('/api/phone-access/start')
    async def phone_access_start(body:WifiSetup,request:Request):
        if request.headers.get('origin') not in LOCAL:raise HTTPException(403,'Enable phone access from the home computer’s local TQIG page.')
        try:return await phone_access.start()
        except Exception as exc:raise HTTPException(409,connection_error(exc)) from None

    @app.post('/api/phone-access/stop')
    async def phone_access_stop(request:Request):
        if request.headers.get('origin') not in LOCAL:raise HTTPException(403,'Turn off phone access from the home computer’s local TQIG page.')
        await phone_access.stop()
        return phone_access.status()

    @app.get('/authorize',response_class=HTMLResponse)
    async def authorize():
        return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Authorize TQIG</title><body style="background:#0b0c13;color:#eee;font:16px system-ui;max-width:600px;margin:12vh auto;padding:30px"><h1>Connect your browser.</h1><p>Copy this temporary helper code into TQIG’s connection wizard. Keep it private. It expires when this helper restarts.</p><input aria-label="Temporary helper code" readonly style="width:100%;padding:14px;font:14px monospace" value="'+token+'"><p>This is a local access code, not an Apple pairing record. Apple credentials stay on this computer.</p><p><a style="color:#baabff" href="/dashboard">Use the local TQIG dashboard →</a></p><p><a style="color:#baabff" href="/recovery">Local Stop / Restore controls →</a></p></body></html>'

    @app.get('/recovery',response_class=HTMLResponse)
    async def recovery():
        # Physical-computer recovery stays available during account or cloud outages.
        return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>TQIG local recovery</title>
        <body style="background:#0b0d16;color:#e9e1f2;font:15px system-ui;max-width:650px;margin:10vh auto;padding:28px">
        <h1>Return to normal location.</h1><p>These controls work only through this computer's local helper. They remain available when the account service is offline.</p>
        <p>Keep the trusted iPhone connected and unlocked. If Wi-Fi cannot open its developer channel, reconnect USB and verify that connection in TQIG.</p>
        <button onclick="run('stop')" style="padding:14px;margin:10px 8px 10px 0">Stop Simulation / Restore</button>
        <button onclick="run('disconnect')" style="padding:14px">Stop and disconnect</button><p id="message" role="status"></p>
        <p>A clear command is not a GPS readback. Confirm real location in an iPhone app.</p><a href="/authorize" style="color:#c7a5f4">Authorize a browser</a>
        <script>const key='''+json.dumps(token)+''';async function run(action){let message=document.getElementById('message');message.textContent='Sending…';try{let r=await fetch('/api/'+action,{method:'POST',headers:{'Content-Type':'application/json','X-TQIG-Token':key},body:'{}'});let data=await r.json();message.textContent=r.ok?'Clear command sent. Connection: '+data.connection+'. Confirm the iPhone’s real location.':data.detail}catch{message.textContent='Helper unavailable. Reconnect the phone and reopen TQIG.'}}</script></body></html>'''

    @app.get('/api/status')
    async def status(): return snapshot()

    @app.get('/api/capabilities')
    async def capabilities(): return snapshot()['capabilities']

    @app.get('/api/devices')
    async def devices(transport:str='usb'):
        if transport not in adapters: raise HTTPException(400,'Choose USB or Wi-Fi.')
        try:
            device.state='discovering' if device.connection!='connected' else device.state
            records=await asyncio.wait_for(adapters[transport].discover(),10)
            return {'devices':records,'transport':transport}
        except Exception as exc:
            raise HTTPException(503,'Cannot find the iPhone. Check the cable, unlock it and confirm the Apple device service is running. '+str(exc)) from exc
        finally:
            if device.connection!='connected': device.state='disconnected'

    @app.post('/api/connect')
    async def connect(body:ConnectBody):
        async def action():
            if device.connection=='connected': raise RuntimeError('Disconnect the current iPhone first.')
            adapter=adapters[body.transport]
            if not injected:
                device.factory,device.discovery=adapter.open,adapter.discover
            await device.connect(body.id)
            remote.remember_transport(body.id,body.transport)
            return snapshot()
        return await perform(action)

    @app.post('/api/location')
    async def location(body:Coordinates):
        async def action():
            if playback.state in {'playing','starting','paused'}: raise RuntimeError('Stop the journey before setting a stationary location.')
            await device.command('set',body.lat,body.lng)
            return snapshot()
        return await perform(action)

    @app.post('/api/wifi/setup')
    async def wifi_setup(body:WifiSetup):
        async def action():
            if not device.device or device.connection!='connected' or device.device.get('transport')!='USB':
                raise RuntimeError('First connect and verify your iPhone over USB.')
            result=await enable_wifi(device.device['id'])
            if not injected:adapters['wifi'].remember_device(device.device['id'])
            return {**snapshot(),'wifiSetup':result}
        return await perform(action)

    @app.post('/api/wifi/address')
    async def wifi_address(body:WifiAddress):
        if device.connection=='connected':raise HTTPException(409,'Disconnect the active session before changing the Wi-Fi address.')
        target=device.device or adapters['wifi'].manual
        if not target:raise HTTPException(409,'Verify this iPhone over USB before configuring its Wi-Fi address.')
        try:adapters['wifi'].configure(target['id'],body.address)
        except ValueError:raise HTTPException(400,'Enter the iPhone’s private IP address on your trusted shared network.') from None
        return snapshot()

    @app.post('/api/stop')
    async def stop():
        async def action():
            await playback.stop(clear=False)
            await device.command('stop')
            return snapshot()
        return await perform(action)

    @app.post('/api/disconnect')
    async def disconnect():
        async def action():
            await playback.stop(clear=False)
            await device.command('disconnect')
            return snapshot()
        return await perform(action)

    @app.post('/api/journey/start')
    async def start(body:RouteBody):
        async def action():
            await playback.start([f.model_dump() for f in body.frames],body.name,body.playbackRate,body.trip.model_dump() if body.trip else None)
            return snapshot()
        return await perform(action)

    for endpoint,method in [('pause',playback.pause),('resume',playback.resume),('stop',playback.stop)]:
        def route_factory(op):
            async def route():
                async def action():
                    await op()
                    return snapshot()
                return await perform(action)
            return route
        app.post('/api/journey/'+endpoint)(route_factory(method))

    async def execute_remote(action,payload):
        if action=='connect':
            if device.connection=='connected':return snapshot()
            return await connect(ConnectBody.model_validate(payload))
        if action=='location':return await location(Coordinates.model_validate(payload))
        if action=='journey/start':return await start(RouteBody.model_validate(payload))
        if action=='stop':return await stop()
        if action=='disconnect':return await disconnect()
        methods={'journey/pause':playback.pause,'journey/resume':playback.resume,'journey/stop':playback.stop}
        if action not in methods:raise ValueError('Unsupported remote action.')
        async def update():await methods[action]();return snapshot()
        return await perform(update)

    remote=RemoteAgent(snapshot,execute_remote)

    @app.get('/api/remote/info')
    async def remote_info():return remote.public()

    @app.post('/api/remote/link')
    async def remote_link(body:RemoteLink):
        if device.connection!='connected' or not device.device:raise HTTPException(409,'First connect and verify the iPhone locally, then link this computer.')
        try:await remote.link(body.code,device.device['id'],'wifi' if device.device['transport']=='Wi-Fi' else 'usb')
        except (OSError,ValueError,RuntimeError):raise HTTPException(409,'Computer linking failed. Check the account server and use a fresh five-minute link code.') from None
        return snapshot()

    @app.post('/api/remote/unlink')
    async def remote_unlink():
        await remote.close(unlink=True)
        return snapshot()

    @app.post('/api/portable/observation')
    async def portable(body:PortableObservation):
        nonlocal portable_observation
        if device.connection=='connected' or not device.last_accepted:
            raise HTTPException(409,'This observation requires a previously applied location and an unplugged device.')
        portable_observation={**body.model_dump(),'source':'user-observed','os':device.device.get('ios') if device.device else None}
        # A brief persistence observation is evidence only, not a permanent offline capability guarantee.
        return snapshot()

    @app.websocket('/api/events')
    async def events(ws:WebSocket):
        if ws.headers.get('host') not in HOSTS or ws.headers.get('origin') not in ORIGINS:
            await ws.close(code=1008); return
        await ws.accept()
        try:
            auth=await asyncio.wait_for(ws.receive_json(),5)
            if not secrets.compare_digest(str(auth.get('token','')),token):
                await ws.close(code=1008); return
            while True:
                await ws.send_json(snapshot())
                await asyncio.sleep(.5)
        except (WebSocketDisconnect,asyncio.TimeoutError,RuntimeError): pass

    if DIST.exists(): app.mount('/assets',StaticFiles(directory=DIST/'assets',check_dir=False),name='assets')
    @app.get('/{path:path}')
    async def website(path:str):
        if path.startswith('api/'): raise HTTPException(404)
        asset=(DIST/path).resolve()
        if asset.is_relative_to(DIST.resolve()) and asset.is_file(): return FileResponse(asset)
        if (DIST/'index.html').exists(): return FileResponse(DIST/'index.html')
        return HTMLResponse('<h1>Build TQIG first</h1><p>Run npm run build, then restart the helper.</p>',503)
    return app

app=create_app()
if __name__=='__main__':
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app,host='127.0.0.1',port=PORT,proxy_headers=False,access_log=False)
