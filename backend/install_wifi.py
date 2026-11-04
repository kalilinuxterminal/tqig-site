"""Prepare a separate supported Wi-Fi runtime; leave the USB runtime intact."""
import json
import ssl
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'.runtime'

def install():
    base=sys.executable if hasattr(ssl.SSLContext,'set_psk_client_callback') else None
    if base is None:
        for version in ['3.14','3.13']:
            try:
                found=subprocess.run(['py','-'+version,'-c','import sys,ssl; assert hasattr(ssl.SSLContext,"set_psk_client_callback"); print(sys.executable)'],capture_output=True,text=True,timeout=10)
                if found.returncode==0:base=found.stdout.strip();break
            except (OSError,subprocess.TimeoutExpired):pass
    if base is None:raise RuntimeError('Install an official OpenSSL-based Python 3.13+ runtime, then run Wi-Fi setup again. USB remains available.')
    folder=PRIVATE/'wifi-venv';python=folder/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    if not python.exists():subprocess.run([base,'-m','venv',str(folder)],check=True)
    subprocess.run([str(python),'-m','pip','install','pymobiledevice3==11.45.1'],check=True)
    check=subprocess.run([str(python),'-c','import ssl,pymobiledevice3; assert hasattr(ssl.SSLContext,"set_psk_client_callback")'],capture_output=True,timeout=15)
    if check.returncode:raise RuntimeError('The Wi-Fi runtime failed its transport check.')
    (PRIVATE/'wifi-runtime.json').write_text(json.dumps({'python':str(python.resolve())}),encoding='utf-8')
    print('Isolated Wi-Fi runtime ready. The USB runtime was preserved.')

if __name__=='__main__':install()
