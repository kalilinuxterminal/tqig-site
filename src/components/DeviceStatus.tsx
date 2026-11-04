import {Cable,Wifi} from 'lucide-react';
import type {DeviceSession} from '../hooks/useDevice';
export function DeviceStatus({device,onClick}:{device:DeviceSession;onClick:()=>void}){const ready=device.online&&device.status.connection==='connected';return <button className={'device-pill '+(ready?'connected':'')} onClick={onClick}>{device.status.device?.transport==='Wi-Fi'?<Wifi size={15}/>:<Cable size={15}/>}<span>{ready?device.status.device?.name:device.online?'Connect iPhone':'Start local helper'}</span><i className={ready?'status-dot':'status-dot off'}/></button>}
