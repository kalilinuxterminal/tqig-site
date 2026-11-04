"""Real USB -> lockdown -> userspace RSD -> DVT adapter. No geolocation mocks."""
import asyncio
from contextlib import asynccontextmanager

SUPPORTED_USB_VERSIONS = frozenset({"26.6", "26.7.2"})


async def discover():
    from pymobiledevice3.usbmux import list_devices
    devices = await asyncio.wait_for(list_devices(), 8)
    return [{"id": d.serial, "transport": "USB"} for d in devices if d.connection_type == "USB"]


@asynccontextmanager
async def open_device(udid, on_phase=lambda phase: None):
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
    from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
    from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

    if udid not in {d["id"] for d in await discover()}:
        raise RuntimeError("Selected iPhone is not attached over USB.")
    on_phase('pairing')
    async with await create_using_usbmux(serial=udid, connection_type="USB", pair_timeout=45) as lockdown:
        values = lockdown.all_values
        version = values.get("ProductVersion", "unknown")
        if not str(values.get("ProductType", "")).startswith("iPhone"):
            raise RuntimeError("This proof targets an iPhone, not another Apple device.")
        if version not in SUPPORTED_USB_VERSIONS:
            raise RuntimeError(f"Device reports iOS {version}. This USB adapter supports iOS 26.6 and 26.7.2.")
        developer_mode = await lockdown.get_value(domain="com.apple.security.mac.amfi", key="DeveloperModeStatus")
        if developer_mode is not True:
            raise RuntimeError("Developer Mode is off. Enable it in iPhone Settings > Privacy & Security > Developer Mode, complete the phone's restart/confirmation, unlock it, then reconnect.")
        # No Wi-Fi/RemotePairing fallback. Only the selected USB device is allowed.
        on_phase('connecting')
        async with UserspaceRsdTunnel(serial=udid, autopair=True, remotepairing_fallback=False) as rsd:
            async with DvtProvider(rsd) as dvt, LocationSimulation(dvt) as location:
                async def ping():
                    if udid not in {d["id"] for d in await discover()}:
                        raise ConnectionError("Selected iPhone was unplugged.")
                    await lockdown.get_value(key="ProductVersion")
                yield location, ping, {
                    "id": udid, "name": values.get("DeviceName", "iPhone"),
                    "ios": version, "build": values.get("BuildVersion", "unknown"),
                    "model": values.get("ProductType"), "transport": "USB",
                }
