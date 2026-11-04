"""Install a checksum-pinned official Cloudflare client locally; no Windows service or firewall edits."""
import hashlib
import os
import urllib.request
from pathlib import Path

VERSION='2026.10.0'
SHA256='86aee4017b26625cee8484c113558f48effa4cd47f7aa05fcf425604e5d2b23c'
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'.runtime'/'tools'/'cloudflared.exe'

def install():
    if os.name!='nt':raise RuntimeError('This portable phone-access installer targets Windows x64.')
    if BINARY.exists() and hashlib.sha256(BINARY.read_bytes()).hexdigest()==SHA256:return
    BINARY.parent.mkdir(parents=True,exist_ok=True)
    staged=BINARY.with_suffix('.download')
    try:
        url=f'https://github.com/cloudflare/cloudflared/releases/download/{VERSION}/cloudflared-windows-amd64.exe'
        request=urllib.request.Request(url,headers={'User-Agent':'TQIG-phone-access'})
        with urllib.request.urlopen(request,timeout=40) as source,staged.open('wb') as target:
            while chunk:=source.read(1024*1024):target.write(chunk)
        if hashlib.sha256(staged.read_bytes()).hexdigest()!=SHA256:raise RuntimeError('Official client checksum did not match. Nothing was installed.')
        staged.replace(BINARY)
    finally:staged.unlink(missing_ok=True)

if __name__=='__main__':
    install()
    print('Verified phone-access component is ready. No service, firewall or network profile was changed.')
