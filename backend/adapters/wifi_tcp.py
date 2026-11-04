"""Paired LAN fallback using pymobiledevice3's TCP lockdown and userspace tunnel APIs."""
from contextlib import asynccontextmanager
from pymobiledevice3.lockdown import create_using_tcp
from pymobiledevice3.pair_records import get_usbmux_pairing_record
from pymobiledevice3.remote import tunnel_service
from pymobiledevice3.remote.userspace_tunnel import UserspaceDialPlane
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService


async def trusted_tcp(address, device_id):
    record=await get_usbmux_pairing_record(device_id)
    if not record:raise RuntimeError('The trusted Apple pairing record is unavailable. Pair over USB first.')
    client=await create_using_tcp(address,identifier=device_id,pair_record=record,autopair=False,keep_alive=True)
    if not client.paired or client.udid!=device_id:
        await client.close()
        raise RuntimeError('This address did not authenticate as the previously trusted iPhone.')
    return client


@asynccontextmanager
async def paired_tcp_rsd(lockdown,on_phase=lambda value:None):
    # DeviceController owns a single session in one task. This pinned upstream switch
    # selects its root-free userspace transport, exactly as UserspaceRsdTunnel does.
    previous=tunnel_service.USE_USERSPACE_TUNNEL
    tunnel_service.USE_USERSPACE_TUNNEL=True
    provider=None
    try:
        provider=await tunnel_service.CoreDeviceTunnelProxy.create(lockdown)
        on_phase("CoreDeviceProxy opened")
        async with provider.start_tcp_tunnel() as transport:
            on_phase("TCP tunnel negotiated")
            transport.client.tun.set_peer(transport.address)
            async with UserspaceDialPlane(transport.client.tun,transport.address) as plane:
                rsd=RemoteServiceDiscoveryService((transport.address,transport.port),open_connection=plane.dial,auxiliary_metadata=transport.auxiliary_metadata)
                try:
                    on_phase("Connecting remote discovery")
                    await rsd.connect()
                    yield rsd
                finally:await rsd.close()
    finally:
        if provider:await provider.close()
        tunnel_service.USE_USERSPACE_TUNNEL=previous
