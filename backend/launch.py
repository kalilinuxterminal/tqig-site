"""Run the local account website and device helper together, with coordinated shutdown."""
import asyncio
import signal
from contextlib import contextmanager
import uvicorn
from backend.main import app as helper
from backend.portal import app as portal

class LocalServer(uvicorn.Server):
    @contextmanager
    def capture_signals(self):yield

async def main():
    servers=[LocalServer(uvicorn.Config(helper,host='127.0.0.1',port=8766,access_log=False)),
             LocalServer(uvicorn.Config(portal,host='127.0.0.1',port=8770,access_log=False))]
    def stop(*args):
        for server in servers:server.should_exit=True
    signal.signal(signal.SIGINT,stop)
    if hasattr(signal,'SIGTERM'):signal.signal(signal.SIGTERM,stop)
    print('TQIG: http://127.0.0.1:8766/dashboard',flush=True)
    print('First launch: open /owner/setup and create your owner account. No default password exists.',flush=True)
    print('Keep this window open for local and remote device control. Ctrl+C closes both services.',flush=True)
    await asyncio.gather(*(server.serve() for server in servers))

if __name__=='__main__':asyncio.run(main())
