from contextlib import asynccontextmanager
import asyncio
import ipaddress
import json
from pathlib import Path
from backend.adapters.base import DeviceConnectionAdapter

class WifiDeviceAdapter(DeviceConnectionAdapter):
    """Experimental Network-only path. Never silently call a cabled connection Wi-Fi."""
    id = 'wifi'
    def __init__(self,load_settings=True,path=None):
        self.manual=None
        self.target_id=None
        self.path=Path(path) if path else Path(__file__).resolve().parents[2]/'.runtime'/'wifi-address.json'
        try:
            value=json.loads(self.path.read_text(encoding='utf-8')) if load_settings else {}
            if ipaddress.ip_address(value['address']).is_private:self.manual=value
        except (OSError,ValueError,KeyError):pass
        if load_settings:
            try:self.target_id=json.loads(self.path.with_name('wifi-target.json').read_text())['id']
            except (OSError,ValueError,KeyError):pass

    def remember_device(self,device_id):
        self.target_id=device_id
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.with_name('wifi-target.json').write_text(json.dumps({'id':device_id}),encoding='utf-8')

    def configure(self,device_id,address):
        ip=ipaddress.ip_address(address)
        if not ip.is_private or ip.is_loopback or ip.is_unspecified:raise ValueError('Use the iPhone’s private address on the trusted shared network.')
        self.manual={'id':device_id,'address':str(ip)}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(self.manual),encoding='utf-8');self.path.chmod(0o600)

    async def discover(self):
        from pymobiledevice3.usbmux import list_devices
        records = await list_devices()
        usb_ids = {d.serial for d in records if d.connection_type == 'USB'}
        found=[{'id': d.serial, 'transport': 'Wi-Fi'} for d in records
                if d.connection_type == 'Network' and d.serial not in usb_ids]
        target=self.manual['id'] if self.manual else self.target_id
        if target and target not in usb_ids:
            from pymobiledevice3.remote.tunnel_service import get_remote_pairing_tunnel_services
            providers=[]
            try:
                providers=await asyncio.wait_for(get_remote_pairing_tunnel_services(bonjour_timeout=3,udid=target),12)
                if providers and target not in {d['id'] for d in found}:found.append({'id':target,'transport':'Wi-Fi'})
            except (OSError,RuntimeError,ValueError,asyncio.TimeoutError):pass
            finally:
                for provider in providers:await provider.close()
        if self.manual and self.manual['id'] not in usb_ids and self.manual['id'] not in {d['id'] for d in found}:
            from backend.adapters.wifi_tcp import trusted_tcp
            try:
                client=await asyncio.wait_for(trusted_tcp(self.manual['address'],self.manual['id']),6)
                await client.close()
                found.append({'id':self.manual['id'],'transport':'Wi-Fi'})
            except (OSError,RuntimeError,asyncio.TimeoutError):pass
        return found

    @asynccontextmanager
    async def open(self, device_id):
        from backend.adapters.wifi_remote import open_remote_wifi
        async with open_remote_wifi(device_id) as opened:
            yield opened
    def capabilities(self):
        return {'available': True, 'experimental': True, 'requiresHelper': True, 'initialUsbPairing': True,
                'portable': 'unverified', 'offlineControl': False,
                'manualAddress':True,
                'reason': 'Initial USB RemotePairing and the isolated Wi-Fi component are required. The authenticated LAN transport uses no USB fallback; cable-free and cellular behavior require separate checks.'}
