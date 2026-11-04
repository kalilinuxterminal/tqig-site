from backend.adapters.base import DeviceConnectionAdapter, UnavailableTransport

class BrowserUsbAdapter(DeviceConnectionAdapter):
    id = 'browser-usb'
    async def discover(self):
        raise UnavailableTransport('Direct browser iPhone protocols are not implemented. Use the Windows helper with USB.')
    def open(self, device_id):
        raise UnavailableTransport('A USB permission picker alone cannot establish this implementation’s developer session.')
    def capabilities(self):
        return {'available': False, 'requiresHelper': True, 'reason': 'Browser-native pairing/tunnel/DVT integration has not been validated.'}
