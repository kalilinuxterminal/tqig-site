"""One isolated, explicitly network-only developer session. IPC accepts location operations only."""
import asyncio
import ipaddress
import json
import logging
import socket
import sys
from pathlib import Path
from contextlib import asynccontextmanager

ROOT=Path(__file__).resolve().parents[1]

def reply(**value):print(json.dumps(value),flush=True)

def lan(host):
    try:
        address=ipaddress.ip_address(host.split('%')[0])
        return address.version==4 and any(address in ipaddress.ip_network(network) for network in ['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16'])
    except ValueError:return False

@asynccontextmanager
async def network_rsd(device_id):
    from pymobiledevice3.remote import tunnel_service as ts
    from pymobiledevice3.remote.userspace_tunnel import UserspaceDialPlane
    from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
    providers=await ts.get_remote_pairing_tunnel_services(bonjour_timeout=4,udid=device_id)
    selected=next((p for p in providers if lan(p.hostname)),None)
    if selected is None:
        cache=ROOT/'.runtime'/'wifi-peer.json'
        try:
            saved=json.loads(cache.read_text(encoding='utf-8'))
            if saved['id']==device_id and lan(saved['host']) and type(saved['port']) is int and 0<saved['port']<65536:
                selected=await ts.create_core_device_tunnel_service_using_remotepairing(device_id,saved['host'],saved['port'],autopair=False)
                providers.append(selected)
        except (OSError,ValueError,KeyError):pass
    if selected is None:
        for provider in providers:await provider.close()
        raise RuntimeError('The paired iPhone is not reachable over Wi-Fi. Keep it unlocked on the shared network, or reconnect USB.')
    previous=ts.USE_USERSPACE_TUNNEL;ts.USE_USERSPACE_TUNNEL=True
    try:
        async with selected.start_tcp_tunnel() as transport:
            transport.client.tun.set_peer(transport.address)
            async with UserspaceDialPlane(transport.client.tun,transport.address) as plane:
                rsd=RemoteServiceDiscoveryService((transport.address,transport.port),open_connection=plane.dial,auxiliary_metadata=transport.auxiliary_metadata)
                closed=asyncio.create_task(transport.client.wait_closed())
                try:
                    await rsd.connect()
                    if rsd.udid!=device_id:raise RuntimeError('The wireless phone identity did not match the trusted device.')
                    if rsd.product_version!='26.6':raise RuntimeError('This release targets iOS 26.6.')
                    (ROOT/'.runtime'/'wifi-peer.json').write_text(json.dumps({'id':device_id,'host':selected.hostname,'port':selected.port}),encoding='utf-8')
                    yield rsd,closed
                finally:
                    closed.cancel();await asyncio.gather(closed,return_exceptions=True)
                    await rsd.close()
    finally:
        for provider in providers:await provider.close()
        ts.USE_USERSPACE_TUNNEL=previous

async def main():
    from backend.contracts import Coordinates
    from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
    from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
    from pymobiledevice3.usbmux import list_devices
    first=json.loads(await asyncio.to_thread(sys.stdin.readline))
    device_id=first.get('id')
    if first.get('op')!='open' or not isinstance(device_id,str):raise RuntimeError('Invalid wireless session request.')
    usb_attached=any(d.serial==device_id and d.connection_type=='USB' for d in await list_devices())
    if usb_attached and not first.get('lanDiagnostic'):raise RuntimeError('Unplug USB before verifying the cable-free connection.')
    async with network_rsd(device_id) as connection:
        rsd,closed=connection
        async with DvtProvider(rsd) as dvt,LocationSimulation(dvt) as location:
            values=rsd.all_values or {}
            reply(ok=True,usbStillAttached=usb_attached,device={'id':device_id,'name':values.get('DeviceName','iPhone'),'ios':rsd.product_version,'build':values.get('BuildVersion','unknown'),'model':values.get('ProductType'),'transport':'Wi-Fi'})
            try:
                while line:=await asyncio.to_thread(sys.stdin.readline):
                    request=json.loads(line);op=request.get('op')
                    if closed.done():raise ConnectionError('Wireless transport closed.')
                    if op=='set':
                        point=Coordinates.model_validate({'lat':request.get('lat'),'lng':request.get('lng')})
                        await location.set(point.lat,point.lng)
                    elif op=='clear':await location.clear()
                    elif op=='ping':
                        if rsd.lockdown:await rsd.lockdown.get_value(key='ProductVersion')
                    elif op=='close':reply(ok=True);break
                    else:raise RuntimeError('Unsupported wireless operation.')
                    reply(ok=True)
            finally:await location.clear()

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    socket.setdefaulttimeout(8)
    try:asyncio.run(main())
    except Exception as exc:
        message=str(exc) if type(exc) is RuntimeError else 'The wireless developer connection closed. Reconnect the trusted iPhone.'
        reply(ok=False,error=message,errorType=type(exc).__name__)
