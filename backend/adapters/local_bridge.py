from backend.adapters.base import DeviceConnectionAdapter
from backend.adapters.device_usb import discover, open_device

async def enable_wifi(device_id):
    from pymobiledevice3.lockdown import create_using_usbmux
    if device_id not in {d['id'] for d in await discover()}:
        raise RuntimeError('Connect this trusted iPhone over USB before enabling wireless access.')
    async with await create_using_usbmux(serial=device_id,connection_type='USB',autopair=False) as lockdown:
        await lockdown.set_enable_wifi_connections(True)
        if not await lockdown.get_enable_wifi_connections():
            raise RuntimeError('The iPhone did not confirm wireless setup.')
        from backend.adapters.wifi_remote import prepare_remote_pairing
        await prepare_remote_pairing(lockdown)
        return {'enabled':True,'remotePairingReady':True,'verifiedNetworkSession':False}

class LocalBridgeAdapter(DeviceConnectionAdapter):
    id = 'usb'
    async def discover(self):
        return await discover()
    def open(self, device_id):
        return open_device(device_id, getattr(self,'on_phase',lambda phase:None))
    def capabilities(self):
        return {'available': True, 'requiresHelper': True, 'simulation': True,
                'portable': 'not-supported-on-tested-usb-build', 'offlineControl': False,
                'evidence': 'Foreground set/restore observed on iOS 26.6/23G71; see compatibility report.'}
