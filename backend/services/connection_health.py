"""Read-only local readiness checks and consumer-facing connection failures."""
import asyncio
import platform
import ssl
import json
from pathlib import Path


def psk_available():
    try:
        settings=Path(__file__).resolve().parents[2]/'.runtime'/'wifi-runtime.json'
        if Path(json.loads(settings.read_text())['python']).is_file():return True
    except (OSError,ValueError,KeyError):pass
    if hasattr(ssl.SSLContext,'set_psk_client_callback'):return True
    try:
        from sslpsk_pmd3.sslpsk import SSLPSKContext
        return SSLPSKContext is not None
    except ImportError:return False


async def connection_health(discover,wireless_address=False):
    checks=[{'key':'helper','title':'Windows helper','state':'pass','description':'The local helper is responding to this browser.'}]
    try:
        devices=await asyncio.wait_for(discover(),9)
        count=len(devices)
        checks.append({'key':'usb','title':'USB connection','state':'pass' if count else 'action','description':f'{count} iPhone'+('s' if count!=1 else '')+' detected. Unlock the intended phone before connecting.' if count else 'No USB iPhone detected. Connect a data cable, unlock the phone and approve Trust.'})
    except Exception:
        checks.append({'key':'usb','title':'USB connection','state':'action','description':'Apple’s device connection service did not respond. Check Apple Mobile Device Support and reconnect the cable.'})
    wifi_ready=psk_available()
    checks.append({'key':'wifi-runtime','title':'Optional Wi-Fi component','state':'pass' if wifi_ready else 'info','description':'The encrypted Wi-Fi transport component is available. Device pairing and its location service still need verification.' if wifi_ready else 'The optional encrypted Wi-Fi transport component is not installed. USB remains available.'})
    checks.append({'key':'wifi-target','title':'Wi-Fi setup','state':'info','description':'A trusted phone address is saved locally. This does not prove the phone is reachable or that wireless GPS control works.' if wireless_address else 'No private phone address is saved. Initial trust and a shared network are required for Wi-Fi.'})
    return {'checks':checks,'runtime':{'python':platform.python_version(),'system':platform.system(),'helper':'0.9.0'},'locationWrites':0}


def connection_error(exc):
    name=type(exc).__name__
    if name in {'ConnectionTerminatedError','ConnectionAbortedError','ConnectionResetError','BrokenPipeError','IncompleteReadError'}:
        return 'The iPhone closed its connection. Keep it unlocked, reconnect, and use USB if Wi-Fi cannot finish verification.'
    if name in {'NotPairedError','InvalidHostIDError','PairingError','InvalidPairRecordError'}:
        return 'This computer is not trusted by the iPhone. Reconnect by USB, unlock the phone and approve Trust.'
    if name in {'PasswordRequiredError','DeviceLockedError','PasscodeRequiredError'}:
        return 'Unlock the iPhone, keep it awake and try the connection again.'
    if name in {'DeveloperModeIsNotEnabledError'}:
        return 'Enable Developer Mode in iPhone Settings, complete its restart and confirmation, then reconnect.'
    if name in {'InvalidServiceError','StartServiceError','RemoteXPCHandshakeTimeoutError'}:
        return 'The iPhone location service could not open. Check Developer Mode and reconnect with USB. A trusted connection alone is not a verified location session.'
    if isinstance(exc,TimeoutError):
        return 'The iPhone did not respond in time. Keep it unlocked and on the same network, or reconnect with USB.'
    if isinstance(exc,ConnectionRefusedError):
        return 'The device connection service is unavailable. Check Apple Mobile Device Support and reconnect the iPhone.'
    # Errors authored by TQIG already explain a specific recovery step.
    if type(exc) is RuntimeError and str(exc):return str(exc)[:600]
    return 'The device action could not finish. Reconnect the trusted iPhone and retry. If its location is uncertain, use Stop / Restore.'
