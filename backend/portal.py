"""Public account website / outbound-agent relay. No Apple device libraries are used here."""
import json
import asyncio
import os
import re
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import Field, field_validator
from backend.accounts import Store
from backend.relay_contracts import safe_status
from backend.contracts import StrictBody, Coordinates, RouteBody

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('TQIG_DATA_DIR',str(ROOT/'.runtime')))


class Credentials(StrictBody):
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=12,max_length=128)
    remember:bool=False
    @field_validator('email')
    @classmethod
    def email_valid(cls,value):
        value=value.strip().casefold()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):raise ValueError('Enter a valid email address.')
        return value

class SignIn(StrictBody):
    # Login accepts the password already assigned to an account. Creation keeps its own rules.
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=1,max_length=128)
    remember:bool=False
    @field_validator('email')
    @classmethod
    def identifier_valid(cls,value):
        value=value.strip().casefold()
        if '@' in value:return Credentials.email_valid(value)
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,31}',value):raise ValueError('Enter your username or email address.')
        return value

class Register(Credentials):
    name:str=Field(min_length=2,max_length=60)
    invitation:str=Field(min_length=10,max_length=100)
    @field_validator('name')
    @classmethod
    def name_valid(cls,value):
        if len(value.strip())<2:raise ValueError('Enter a name with at least two characters.')
        return value.strip()

class OwnerSetup(Credentials):
    name:str=Field(min_length=2,max_length=60)
    nonce:str=Field(min_length=20,max_length=100)
    @field_validator('name')
    @classmethod
    def name_valid(cls,value):return Register.name_valid(value)

class Invitation(StrictBody):
    label:str=Field(min_length=1,max_length=80)
    email:str|None=None
    maxUses:int=Field(ge=1,le=100,default=1)
    hours:int=Field(ge=1,le=720,default=168)
    @field_validator('email')
    @classmethod
    def optional_email(cls,value):return Credentials.email_valid(value) if value else None

class Disabled(StrictBody):
    disabled:bool

class PasswordChange(StrictBody):
    currentPassword:str=Field(min_length=1,max_length=128)
    newPassword:str=Field(min_length=12,max_length=128)

class Enrollment(StrictBody):
    name:str=Field(min_length=2,max_length=60)

class Enroll(StrictBody):
    code:str=Field(min_length=20,max_length=100)

class AgentPoll(StrictBody):
    status:dict

class AgentResult(StrictBody):
    command:str=Field(min_length=8,max_length=100)
    result:dict={}
    error:str|None=Field(default=None,max_length=500)

class Command(StrictBody):
    action:str
    payload:dict={}
    @field_validator('action')
    @classmethod
    def valid_action(cls,value):
        if value not in {'connect','location','stop','disconnect','journey/start','journey/pause','journey/resume','journey/stop'}:raise ValueError('Unsupported remote command.')
        return value


def create_portal(path=None,local_preview=None,public_origin=None):
    local_preview=os.getenv('TQIG_LOCAL_PREVIEW','1')=='1' if local_preview is None else local_preview
    origin=(public_origin or os.getenv('TQIG_PUBLIC_ORIGIN','http://127.0.0.1:8770' if local_preview else 'https://tqig.space')).rstrip('/')
    if not local_preview and not origin.startswith('https://'):raise RuntimeError('Production accounts require an HTTPS origin.')
    allowed={origin}
    if local_preview:allowed|={'http://localhost:8770','http://127.0.0.1:8766','http://localhost:8766','http://127.0.0.1:5174','http://localhost:5174'}
    hosts={value.split('://',1)[1] for value in allowed}
    store=Store(path or DATA/'portal.sqlite3')
    @asynccontextmanager
    async def lifespan(app):
        async def maintain():
            while True:
                await asyncio.to_thread(store.cleanup)
                await asyncio.sleep(60)
        maintenance=asyncio.create_task(maintain())
        try:yield
        finally:
            maintenance.cancel()
            try:await maintenance
            except asyncio.CancelledError:pass
    app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
    app.state.store=store
    setup_nonce=secrets.token_urlsafe(32)
    cookie='tqig_preview_session' if local_preview else '__Host-tqig_session'
    rates=defaultdict(deque)
    app.add_middleware(CORSMiddleware,allow_origins=list(allowed),allow_credentials=True,allow_methods=['GET','POST','OPTIONS'],allow_headers=['Content-Type','X-TQIG-CSRF','Authorization'])

    @app.middleware('http')
    async def boundary(request:Request,call_next):
        host=request.headers.get('host','')
        request_origin=request.headers.get('origin')
        if host not in hosts or request_origin and request_origin not in allowed:return JSONResponse({'detail':'Untrusted website origin.'},403)
        if request.method=='POST':
            agent=request.url.path.startswith('/api/agent/')
            if not agent and request_origin not in allowed:return JSONResponse({'detail':'A trusted website origin is required.'},403)
            if request.headers.get('content-type','').split(';')[0]!='application/json':return JSONResponse({'detail':'JSON request required.'},415)
            if len(await request.body())>5_000_000:return JSONResponse({'detail':'Request too large.'},413)
            # Agent credentials have their own boundary; enrollment is tightly limited too.
            key=(request.client.host if request.client else '',request.url.path)
            limit=10 if request.url.path in {'/api/auth/signin','/api/auth/signup','/api/agent/enroll','/api/auth/owner','/api/account/password'} else 180
            now=time.monotonic();q=rates[key]
            while q and q[0]<now-60:q.popleft()
            if len(q)>=limit:return JSONResponse({'detail':'Too many attempts. Wait a minute and try again.'},429)
            q.append(now)
        response=await call_next(request)
        response.headers.update({'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Content-Security-Policy':"frame-ancestors 'none'; object-src 'none'; base-uri 'self'"})
        return response

    def user_session(request,owner=False,mutate=False):
        session=store.session(request.cookies.get(cookie))
        if not session:raise HTTPException(401,'Sign in to continue.')
        if owner and session['user']['role']!='owner':raise HTTPException(403,'Owner access is required.')
        if mutate and not secrets.compare_digest(request.headers.get('x-tqig-csrf',''),session['csrf']):raise HTTPException(403,'Refresh your session before making changes.')
        return session

    def agent(request):
        auth=request.headers.get('authorization','')
        row=store.agent(auth[7:]) if auth.startswith('Bearer ') else None
        if not row:raise HTTPException(401,'Computer authorization expired or was revoked.')
        return row

    def authenticated(user,remember,tokens=None):
        token,csrf,expires=tokens or store.new_session(user['id'],remember)
        response=JSONResponse({'user':user,'csrf':csrf,'expires':expires,'remember':remember})
        response.set_cookie(cookie,token,httponly=True,secure=not local_preview,samesite='lax',path='/',max_age=30*86400 if remember else None)
        return response

    def fail(exc):raise HTTPException(409,str(exc)) from None

    @app.get('/api/auth/session')
    async def session(request:Request):return store.session(request.cookies.get(cookie)) or {'user':None}

    @app.get('/api/auth/setup')
    async def setup(request:Request):
        permitted=local_preview and request.headers.get('host') in {'127.0.0.1:8770','localhost:8770'} and request.client and request.client.host in {'127.0.0.1','::1','testclient'}
        required=not store.has_owner()
        return {'required':required,'allowed':bool(permitted and required),'nonce':setup_nonce if permitted and required else None}

    @app.post('/api/auth/owner')
    async def owner(body:OwnerSetup,request:Request):
        permission=await setup(request)
        if not permission['allowed'] or not secrets.compare_digest(body.nonce,setup_nonce):raise HTTPException(403,'Initialize the owner locally, or use the server management command.')
        try:user=await asyncio.to_thread(store.create_user,body.email,body.name,body.password,owner=True)
        except ValueError as exc:fail(exc)
        return authenticated(user,body.remember)

    @app.post('/api/auth/signup')
    async def signup(body:Register):
        try:user=await asyncio.to_thread(store.create_user,body.email,body.name,body.password,body.invitation.strip())
        except ValueError as exc:fail(exc)
        return authenticated(user,body.remember)

    @app.post('/api/auth/signin')
    async def signin(body:SignIn):
        if not local_preview and len(body.password) < 12:
            raise HTTPException(401,'Phone access requires a password of at least 12 characters. Update it in Account & security on the home computer.')
        signed_in=await asyncio.to_thread(store.login_session,body.email,body.password,body.remember)
        if not signed_in:raise HTTPException(401,'Username, email or password is incorrect, or this account is unavailable.')
        user,tokens=signed_in
        return authenticated(user,body.remember,tokens)

    @app.post('/api/auth/signout')
    async def signout(request:Request):
        user_session(request,mutate=True)
        store.logout(request.cookies[cookie])
        response=JSONResponse({'signedOut':True});response.delete_cookie(cookie,path='/',secure=not local_preview,httponly=True,samesite='lax')
        return response

    @app.get('/api/admin/users')
    async def users(request:Request):
        user_session(request,owner=True)
        return {'users':store.users()}

    @app.get('/api/account/security')
    async def security(request:Request):
        session=user_session(request)
        return {'sessions':store.browser_sessions(session['user']['id'],request.cookies[cookie])}

    @app.post('/api/account/sessions/others/revoke')
    async def revoke_others(request:Request):
        session=user_session(request,mutate=True)
        return {'revoked':store.revoke_other_sessions(session['user']['id'],request.cookies[cookie])}

    @app.post('/api/account/sessions/{sid}/revoke')
    async def revoke_session(sid:str,request:Request):
        session=user_session(request,mutate=True)
        try:store.revoke_browser_session(session['user']['id'],sid,request.cookies[cookie])
        except ValueError as exc:fail(exc)
        return {'revoked':True}

    @app.post('/api/account/password')
    async def password(body:PasswordChange,request:Request):
        session=user_session(request,mutate=True)
        try:user=await asyncio.to_thread(store.change_password,session['user']['id'],body.currentPassword,body.newPassword)
        except ValueError as exc:fail(exc)
        return authenticated(user,session['remember'])

    @app.post('/api/admin/users/{uid}')
    async def disable(uid:str,body:Disabled,request:Request):
        user_session(request,owner=True,mutate=True)
        try:store.disable(uid,body.disabled)
        except ValueError as exc:fail(exc)
        return {'user':store.user(uid)}

    @app.get('/api/admin/invitations')
    async def invitations(request:Request):
        user_session(request,owner=True)
        return {'invitations':store.invitations()}

    @app.post('/api/admin/invitations')
    async def invitation(body:Invitation,request:Request):
        user_session(request,owner=True,mutate=True)
        return {'code':store.create_invitation(body.label,body.email,body.maxUses,body.hours)}

    @app.post('/api/admin/invitations/{iid}/revoke')
    async def revoke_invite(iid:str,request:Request):
        user_session(request,owner=True,mutate=True);store.revoke_invitation(iid)
        return {'revoked':True}

    @app.get('/api/computers')
    async def computers(request:Request):return {'computers':store.computers(user_session(request)['user']['id'])}

    @app.post('/api/computers/enrollment')
    async def enrollment(body:Enrollment,request:Request):
        uid=user_session(request,mutate=True)['user']['id']
        try:return {'code':store.enrollment(uid,body.name.strip()),'expiresIn':300,'portalUrl':origin}
        except ValueError as exc:fail(exc)

    @app.post('/api/computers/{cid}/revoke')
    async def revoke_computer(cid:str,request:Request):
        uid=user_session(request,mutate=True)['user']['id']
        try:store.revoke_computer(uid,cid)
        except ValueError as exc:fail(exc)
        return {'revoked':True}

    @app.post('/api/computers/{cid}/commands')
    async def command(cid:str,body:Command,request:Request):
        uid=user_session(request,mutate=True)['user']['id']
        try:
            if body.action=='location':Coordinates.model_validate(body.payload)
            elif body.action=='journey/start':RouteBody.model_validate(body.payload)
            elif body.payload:raise ValueError('This action does not accept additional data.')
            return store.queue(uid,cid,body.action,body.payload)
        except ValueError as exc:fail(exc)

    @app.get('/api/commands/{command}')
    async def command_status(command:str,request:Request):
        result=store.command(user_session(request)['user']['id'],command)
        if not result:raise HTTPException(404,'Command not found.')
        return result

    @app.post('/api/agent/enroll')
    async def enroll(body:Enroll):
        try:return store.enroll(body.code)
        except ValueError as exc:fail(exc)

    @app.post('/api/agent/poll')
    async def poll(body:AgentPoll,request:Request):
        return {'command':store.poll(agent(request)['id'],safe_status(body.status))}

    @app.post('/api/agent/result')
    async def result(body:AgentResult,request:Request):
        try:store.complete(agent(request)['id'],body.command,safe_status(body.result),body.error)
        except ValueError as exc:fail(exc)
        return {'recorded':True}

    @app.post('/api/agent/heartbeat')
    async def heartbeat(body:AgentPoll,request:Request):
        store.heartbeat(agent(request)['id'],safe_status(body.status))
        return {'recorded':True}

    @app.post('/api/agent/unlink')
    async def agent_unlink(request:Request):
        row=agent(request);store.revoke_computer(row['user_id'],row['id'])
        return {'revoked':True}

    @app.get('/api/portal/health')
    async def health():return {'service':'TQIG accounts and remote relay','version':'0.9.0','localPreview':local_preview}

    @app.get('/{path:path}')
    async def website(path:str):
        if path.startswith('api/'):raise HTTPException(404)
        dist=ROOT/'dist';asset=(dist/path).resolve()
        if asset.is_relative_to(dist.resolve()) and asset.is_file():return FileResponse(asset)
        if (dist/'index.html').exists():return FileResponse(dist/'index.html')
        return JSONResponse({'detail':'Build the frontend first.'},503)
    return app


app=create_portal()
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host=os.getenv('TQIG_PORTAL_BIND','127.0.0.1'),port=int(os.getenv('TQIG_PORTAL_PORT','8770')),proxy_headers=False,access_log=False)
